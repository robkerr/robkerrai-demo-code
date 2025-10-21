"use client";
import React, { useState, useRef } from "react";

type Entry = {
  userText: string;
  charCount: number;
  asciiSum: number;
};

export default function ChatPage() {
  const [input, setInput] = useState<string>("<QUERY GOES HERE>");
  const [entries, setEntries] = useState<Entry[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleInputChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setInput(e.target.value);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      // if (input.trim() !== "") {
        handleGo();
      // }
    }
  }

  function handleGo() {
    // if (input.trim() === "") return;
    const charCount = input.length;
    const asciiSum = input.split("").reduce((sum, c) => sum + c.charCodeAt(0), 0);
    setEntries([
      ...entries,
      {
        userText: input,
        charCount,
        asciiSum,
      },
    ]);
    setInput("");
    if (textareaRef.current) textareaRef.current.focus();
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0a66c2] via-[#004182] to-[#002447]">
        <div className="absolute top-20 left-20 w-72 h-72 bg-white/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-40 right-32 w-96 h-96 bg-[#0077b5]/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-32 left-1/3 w-80 h-80 bg-white/5 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 min-h-screen flex items-center justify-center p-6">
        <div className="w-full max-w-[80vw]" style={{ minWidth: 0 }}>
          {/* Logo and Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-white mb-3 tracking-tight">
              Snowflake OAuth Integration Test
            </h1>
            <p className="text-white/80 text-lg font-medium">
              Experiment with text input and stats
            </p>
          </div>

          {/* Glassmorphic Card */}
          <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl shadow-2xl overflow-hidden">
            {/* Card Header */}
            <div className="bg-gradient-to-r from-white/20 to-white/10 backdrop-blur-sm p-8 border-b border-white/20">
              <h2 className="text-2xl font-semibold text-white text-center">
                Send SQL Statement to Snowflake
              </h2>
              <p className="text-white/70 text-center mt-2">
                Enter a query against the SHIP_PLAN table to test OAuth.
              </p>
            </div>

            {/* Card Content */}
            <div className="p-8 space-y-6">
              <div className="flex gap-3 items-end">
                <textarea
                  ref={textareaRef}
                  rows={3}
                  value={input}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  placeholder="Type your message..."
                  className="flex-1 resize-vertical p-3 rounded-2xl bg-white/20 text-white placeholder-white/60 font-medium text-lg border border-white/20 focus:outline-none focus:ring-2 focus:ring-[#0a66c2] backdrop-blur-md shadow-inner min-h-[60px]"
                  style={{ minHeight: 60 }}
                />
                <button
                  onClick={handleGo}
                  // disabled={input.trim() === ""}
                  className="h-12 min-w-[60px] px-6 rounded-2xl bg-gradient-to-r from-white to-white/90 text-[#0a66c2] font-semibold text-lg shadow-xl border-0 transition-all duration-300 transform hover:scale-[1.04] hover:from-white/90 hover:to-white/80 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                >
                  Go
                </button>
              </div>

              {entries.length > 0 && (
                <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-5 mt-6 overflow-x-auto">
                  <table className="min-w-full text-white/90 text-base table-fixed break-words">
                    <thead>
                      <tr>
                        <th className="text-left p-2 font-semibold">User Entry</th>
                        <th className="text-right p-2 font-semibold">Char Count</th>
                        <th className="text-right p-2 font-semibold">ASCII Sum</th>
                        <th className="text-right p-2 font-semibold">ASCII Sum</th>
                        <th className="text-right p-2 font-semibold">ASCII Sum</th>
                        <th className="text-right p-2 font-semibold">ASCII Sum</th>
                        <th className="text-right p-2 font-semibold">ASCII Sum</th>
                        <th className="text-right p-2 font-semibold">ASCII Sum</th>
                      </tr>
                    </thead>
                    <tbody>
                      {entries.map((entry, idx) => (
                        <tr key={idx} className="border-t border-white/10">
                          <td className="p-2 whitespace-pre-wrap align-top max-w-[180px] break-words">{entry.userText}</td>
                          <td className="p-2 text-right align-top">{entry.charCount}</td>
                          <td className="p-2 text-right align-top">{entry.asciiSum}</td>
                          <td className="p-2 text-right align-top">{entry.asciiSum}</td>
                          <td className="p-2 text-right align-top">{entry.asciiSum}</td>
                          <td className="p-2 text-right align-top">{entry.asciiSum}</td>
                          <td className="p-2 text-right align-top">{entry.asciiSum}</td>
                          <td className="p-2 text-right align-top">{entry.asciiSum}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Card Footer */}
            <div className="bg-gradient-to-r from-white/5 to-white/10 backdrop-blur-sm p-6 border-t border-white/10">
              <p className="text-white/60 text-xs text-center">
                This is a demo playground. Your text is not saved.
              </p>
            </div>
          </div>

          {/* Bottom Text */}
          <div className="text-center mt-8">
            <p className="text-white/50 text-sm">
            <a
                href="https://robkerr.ai"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-white/80 transition-colors"
            >
                For more info visit robkerr.ai
            </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
