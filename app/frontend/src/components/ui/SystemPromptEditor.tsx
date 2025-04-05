// src/components/ui/SystemPromptEditor.tsx

import React, { useState } from "react";

type SystemPromptEditorProps = {
  onSubmit: (promptValue: string) => void;
};

export default function SystemPromptEditor({ onSubmit }: SystemPromptEditorProps) {
  const [systemPrompt, setSystemPrompt] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setSystemPrompt(e.target.value);
  };

  const handleSubmit = () => {
    if (!systemPrompt.trim()) return;
    onSubmit(systemPrompt);
  };

  return (
    <div className="p-2 w-full max-w-xl bg-white rounded shadow my-4">
      <label className="block text-sm font-bold mb-1" htmlFor="systemPrompt">
        System Prompt
      </label>
      <textarea
        id="systemPrompt"
        value={systemPrompt}
        onChange={handleChange}
        rows={4}
        className="w-full p-2 border border-gray-300 rounded"
        placeholder="ここにシステムプロンプトを入力してください"
      />
      <button
        onClick={handleSubmit}
        className="mt-2 px-4 py-2 bg-blue-600 text-white rounded"
      >
        実行
      </button>
    </div>
  );
}
