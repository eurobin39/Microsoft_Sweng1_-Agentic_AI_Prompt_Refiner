"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Header() {
  const pathname = usePathname();

  const links = [
    { name: "Setup", href: "/setup" },
    { name: "Live", href: "/live" },
    { name: "Refinement", href: "/refinement" },
    { name: "Results", href: "/results" },
    { name: "Details", href: "/details" },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/10 bg-black/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo Area */}
        <Link href="/" className="flex items-center gap-3 opacity-90 hover:opacity-100 transition-opacity">
          <div className="w-8 h-8 rounded-lg bg-white/10 overflow-hidden bg-gradient-to-br from-purple-500 to-blue-500">
             {/* Placeholder for logo until image is available */}
          </div>
          <span className="text-lg font-semibold text-white">PromptLab</span>
        </Link>

        {/* Navigation Links */}
        <div className="flex items-center gap-1 bg-white/5 p-1 rounded-full border border-white/10">
          {links.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`
                  px-4 py-1.5 text-sm rounded-full transition-all duration-300
                  ${isActive 
                    ? "bg-white text-black font-medium shadow-[0_0_15px_rgba(255,255,255,0.2)]" 
                    : "text-gray-400 hover:text-white hover:bg-white/5"
                  }
                `}
              >
                {link.name}
              </Link>
            );
          })}
        </div>
        
        <div className="w-8" /> {/* Spacer for centering */}
      </div>
    </nav>
  );
}