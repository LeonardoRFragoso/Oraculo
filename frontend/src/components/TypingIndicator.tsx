export default function TypingIndicator() {
  return (
    <div className="flex justify-start animate-fade-in">
      <div className="chat-bubble-assistant max-w-[80%]">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl">🔮</span>
          <span className="font-semibold text-primary">Oráculo</span>
        </div>
        
        <div className="flex gap-1.5">
          <div className="w-2 h-2 bg-primary rounded-full animate-typing" />
          <div className="w-2 h-2 bg-primary rounded-full animate-typing" />
          <div className="w-2 h-2 bg-primary rounded-full animate-typing" />
        </div>
      </div>
    </div>
  )
}
