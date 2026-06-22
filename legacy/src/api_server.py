"""
API REST para integração do GPTRACKER com sistemas externos
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import pandas as pd
from datetime import datetime, timedelta
import os
from .auth import AuthManager
from .budget_manager import BudgetManager
from .data_loader import carregar_planilhas
import json

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'gptracker_api_secret_2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)

jwt = JWTManager(app)
CORS(app)

# Instâncias dos gerenciadores
auth_manager = AuthManager()
budget_manager = BudgetManager()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de verificação de saúde da API"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Endpoint de autenticação"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username and password required'}), 400
    
    username = data['username']
    password = data['password']
    
    if auth_manager.authenticate(username, password):
        access_token = create_access_token(identity=username)
        user_info = auth_manager.get_user_info(username)
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'username': username,
                'role': user_info.get('role', 'user'),
                'permissions': user_info.get('permissions', [])
            }
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/data/containers', methods=['GET'])
@jwt_required()
def get_containers_data():
    """Endpoint para obter dados de containers"""
    try:
        # Parâmetros de filtro
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        cliente = request.args.get('cliente')
        operacao = request.args.get('operacao')
        
        # Carregar dados
        df = carregar_planilhas()
        
        if df.empty:
            return jsonify({'error': 'No data available'}), 404
        
        # Aplicar filtros
        if ano:
            df = df[df['ano'] == ano]
        if mes:
            df = df[df['mes'] == mes]
        if cliente:
            df = df[df['cliente'].str.contains(cliente, case=False, na=False)]
        if operacao:
            df = df[df['tipo_operacao'] == operacao]
        
        # Agregar dados
        result = {
            'total_containers': int(df['qtd_container'].sum()),
            'total_operacoes': len(df),
            'clientes_unicos': int(df['cliente'].nunique()) if 'cliente' in df.columns else 0,
            'por_operacao': df.groupby('tipo_operacao')['qtd_container'].sum().to_dict() if 'tipo_operacao' in df.columns else {},
            'filtros_aplicados': {
                'ano': ano,
                'mes': mes,
                'cliente': cliente,
                'operacao': operacao
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/budget/performance', methods=['GET'])
@jwt_required()
def get_budget_performance():
    """Endpoint para obter performance vs budget"""
    try:
        username = get_jwt_identity()
        if not auth_manager.has_permission(username, 'budget'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        df = carregar_planilhas()
        comparison = budget_manager.get_budget_vs_actual(df)
        
        return jsonify(comparison)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/budget/goals', methods=['POST'])
@jwt_required()
def set_budget_goals():
    """Endpoint para definir metas de budget"""
    try:
        username = get_jwt_identity()
        if not auth_manager.has_permission(username, 'budget'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        if 'tipo' not in data:
            return jsonify({'error': 'Goal type required'}), 400
        
        if data['tipo'] == 'anual':
            budget_manager.set_annual_goals(
                data['ano'],
                data['receita_total'],
                data['containers_total'],
                data['novos_clientes'],
                data.get('margem_lucro', 0.15)
            )
        elif data['tipo'] == 'mensal':
            budget_manager.set_monthly_goals(
                data['ano'],
                data['mes'],
                data['receita'],
                data['containers']
            )
        elif data['tipo'] == 'cliente':
            budget_manager.set_client_goals(
                data['cliente'],
                data['receita_anual'],
                data['containers_anuais']
            )
        
        return jsonify({'message': 'Goals set successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/opportunities', methods=['GET'])
@jwt_required()
def get_opportunities():
    """Endpoint para obter oportunidades comerciais"""
    try:
        username = get_jwt_identity()
        if not auth_manager.has_permission(username, 'analytics'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        df = carregar_planilhas()
        opportunities = budget_manager.get_opportunities(df)
        
        return jsonify({'opportunities': opportunities})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/trends', methods=['GET'])
@jwt_required()
def get_trends():
    """Endpoint para análise de tendências"""
    try:
        df = carregar_planilhas()
        
        if df.empty or 'ano_mes' not in df.columns:
            return jsonify({'error': 'Insufficient data for trend analysis'}), 404
        
        # Dados mensais
        monthly_data = df.groupby('ano_mes').agg({
            'qtd_container': 'sum',
            'cliente': 'nunique'
        }).reset_index()
        
        monthly_data['data'] = pd.to_datetime(monthly_data['ano_mes'].astype(str), format='%Y%m')
        monthly_data = monthly_data.sort_values('data')
        
        # Converter para formato JSON serializable
        trends = {
            'monthly_containers': [
                {
                    'periodo': row['ano_mes'],
                    'data': row['data'].isoformat(),
                    'containers': int(row['qtd_container']),
                    'clientes': int(row['cliente'])
                }
                for _, row in monthly_data.iterrows()
            ]
        }
        
        # Calcular tendência
        if len(monthly_data) >= 3:
            recent_trend = monthly_data.tail(3)
            if recent_trend['qtd_container'].iloc[-1] > recent_trend['qtd_container'].iloc[0]:
                trends['tendencia'] = 'crescimento'
            else:
                trends['tendencia'] = 'queda'
        else:
            trends['tendencia'] = 'insuficiente'
        
        return jsonify(trends)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clients/top', methods=['GET'])
@jwt_required()
def get_top_clients():
    """Endpoint para obter top clientes"""
    try:
        limit = request.args.get('limit', 10, type=int)
        ano = request.args.get('ano', type=int)
        
        df = carregar_planilhas()
        
        if df.empty or 'cliente' not in df.columns:
            return jsonify({'error': 'No client data available'}), 404
        
        # Filtrar por ano se especificado
        if ano:
            df = df[df['ano'] == ano]
        
        # Top clientes
        top_clients = df.groupby('cliente').agg({
            'qtd_container': 'sum',
            'ano_mes': 'count'  # número de operações
        }).reset_index()
        
        top_clients.columns = ['cliente', 'total_containers', 'num_operacoes']
        top_clients = top_clients.sort_values('total_containers', ascending=False).head(limit)
        
        result = [
            {
                'cliente': row['cliente'],
                'total_containers': int(row['total_containers']),
                'num_operacoes': int(row['num_operacoes'])
            }
            for _, row in top_clients.iterrows()
        ]
        
        return jsonify({'top_clients': result})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/upload', methods=['POST'])
@jwt_required()
def upload_data():
    """Endpoint para upload de novos dados"""
    try:
        username = get_jwt_identity()
        if not auth_manager.has_permission(username, 'write'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Salvar arquivo temporariamente
        filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join('uploads', filename)
        
        os.makedirs('uploads', exist_ok=True)
        file.save(filepath)
        
        # Processar arquivo (implementar lógica específica)
        # Por enquanto, apenas confirmar recebimento
        
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'uploaded_by': username,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Inicializar usuários padrão
    auth_manager.init_default_users()
    
    # Executar servidor
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('API_PORT', 5000)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )
