"use client";
import Link from "next/link";

export default function Home() {
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
        <div className="w-full max-w-[80vw] md:max-w-xl">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-white mb-3 tracking-tight">
              Snowflake Integration Testing
            </h1>
          </div>

          <div className="overflow-hidden p-10">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
              <Link
                href="/query"
                className="h-40 flex items-center justify-center rounded-2xl bg-gradient-to-r from-[#3b82f6] to-[#3b82f6] text-white font-bold text-3xl shadow-xl border-0 transition-all duration-300 transform hover:scale-[1.04] hover:from-[#2563eb] hover:to-[#1e3a8a] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none text-center"
              >
                SQL Query
              </Link>
              <Link
                href="/"
                className="h-40 flex items-center justify-center rounded-2xl bg-gradient-to-r from-[#3b82f6] to-[#3b82f6] text-white font-bold text-3xl shadow-xl border-0 transition-all duration-300 transform hover:scale-[1.04] hover:from-[#2563eb] hover:to-[#1e3a8a] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none text-center"
              >
                Page2
              </Link>
              <Link
                href="/"
                className="h-40 flex items-center justify-center rounded-2xl bg-gradient-to-r from-[#3b82f6] to-[#3b82f6] text-white font-bold text-3xl shadow-xl border-0 transition-all duration-300 transform hover:scale-[1.04] hover:from-[#2563eb] hover:to-[#1e3a8a] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none text-center"
              >
                Page3
              </Link>
              <Link
                href="/"
                className="h-40 flex items-center justify-center rounded-2xl bg-gradient-to-r from-[#3b82f6] to-[#3b82f6] text-white font-bold text-3xl shadow-xl border-0 transition-all duration-300 transform hover:scale-[1.04] hover:from-[#2563eb] hover:to-[#1e3a8a] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none text-center"
              >
                Page4
              </Link>
              <Link
                href="/"
                className="h-40 flex items-center justify-center rounded-2xl bg-gradient-to-r from-[#3b82f6] to-[#3b82f6] text-white font-bold text-3xl shadow-xl border-0 transition-all duration-300 transform hover:scale-[1.04] hover:from-[#2563eb] hover:to-[#1e3a8a] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none text-center"
              >
                Page5
              </Link>
              <Link
                href="/"
                className="h-40 flex items-center justify-center rounded-2xl bg-gradient-to-r from-[#3b82f6] to-[#3b82f6] text-white font-bold text-3xl shadow-xl border-0 transition-all duration-300 transform hover:scale-[1.04] hover:from-[#2563eb] hover:to-[#1e3a8a] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none text-center"
              >
                Page6
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
