"use client";

import { useState, useEffect } from "react";

export default function PromptLabLanding() {
  const [scrollY, setScrollY] = useState(0);
  const [mounted, setMounted] = useState(false);
  const [isVisible, setIsVisible] = useState({
    hero: false,
    feature1: false,
    feature2: false,
    feature3: false,
    integration: false,
  });

  useEffect(() => {
    setMounted(true);
    
    const handleScroll = () => {
      const y = window.scrollY;
      setScrollY(y);
      
      // Trigger visibility for fade-in animations
      const windowHeight = window.innerHeight;
      
      setIsVisible({
        hero: true,
        feature1: y > windowHeight * 0.2,
        feature2: y > windowHeight * 1.0,
        feature3: y > windowHeight * 1.8,
        integration: y > windowHeight * 2.6,
      });
    };
    
    // Initial check
    handleScroll();
    
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Prevent SSR issues
  if (!mounted) {
    return null;
  }

  return (
    <div className="bg-black text-white">
      
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/10 bg-black/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 md:px-12 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3 transition-transform duration-300 hover:scale-105 cursor-pointer">
            <div className="w-8 h-8 rounded-lg overflow-hidden">
              <img src="/PromptLabLogo.jpg" alt="PromptLab" className="w-full h-full object-cover" />
            </div>
            <span className="text-lg font-semibold">PromptLab</span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm text-gray-400 hover:text-white transition-colors duration-300">Features</a>
            <a href="#platform" className="text-sm text-gray-400 hover:text-white transition-colors duration-300">Platform</a>
            <a href="#docs" className="text-sm text-gray-400 hover:text-white transition-colors duration-300">Docs</a>
            <button className="px-4 py-2 bg-white text-black text-sm font-medium rounded-lg hover:bg-gray-200 transition-all duration-300">
              Get Started
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="min-h-screen flex items-center justify-center px-6 md:px-12 relative overflow-hidden">
        {/* Grid Background */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff08_1px,transparent_1px),linear-gradient(to_bottom,#ffffff08_1px,transparent_1px)] bg-[size:4rem_4rem]" />
        
        {/* Gradient Orb */}
        <div 
          className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-white/5 rounded-full blur-3xl pointer-events-none"
          style={{ transform: `translate(-50%, ${scrollY * 0.3}px)` }}
        />

        <div className={`relative max-w-5xl mx-auto text-center z-10 transition-all duration-1000 ${
          isVisible.hero ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}>
          <div className="mb-8 inline-flex items-center gap-2 px-4 py-2 bg-white/5 rounded-full border border-white/10">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-xs uppercase tracking-wider text-gray-400">Multi-Model Prompt Refinement</span>
          </div>

          <h1 className="text-6xl md:text-8xl font-bold mb-8 leading-[1.1] tracking-tight">
            Build Reliable
            <br />
            <span className="text-gray-500">AI Agents</span>
          </h1>

          <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto">
            Evaluate, refine, and optimize prompts through multi-model consensus.
            <br />From setup to production in minutes.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button className="w-full sm:w-auto px-8 py-4 bg-white text-black font-medium rounded-lg hover:bg-gray-200 transition-all duration-300 hover:scale-105">
              Start Building
            </button>
            <button className="w-full sm:w-auto px-8 py-4 border border-white/20 rounded-lg hover:bg-white/5 transition-all duration-300 flex items-center justify-center gap-2 group">
              <span>View Demo</span>
              <svg className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>

          {/* Scroll Indicator */}
          <div className="absolute top-130 left-1/2 -translate-x-1/2 animate-bounce">
            <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
          </div>
        </div>
      </section>

      {/* Feature Section 1 - Multi-Model Analysis */}
      <section id="features" className="min-h-screen flex items-center px-6 md:px-12 relative">
        <div className={`max-w-7xl mx-auto grid md:grid-cols-2 gap-16 items-center w-full transition-all duration-1000 ${
          isVisible.feature1 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-20'
        }`}>
          <div>
            <div className="mb-6 text-sm uppercase tracking-wider text-gray-500">Intelligent Analysis</div>
            <h2 className="text-5xl md:text-6xl font-bold mb-6">
              Multi-Model
              <br />
              Consensus
            </h2>
            <p className="text-lg text-gray-400 mb-8 leading-relaxed">
              Evaluate prompts across GPT-4, Mistral, and Grok simultaneously. 
              Our ensemble approach eliminates single-point failures and provides 
              consensus-driven insights you can trust.
            </p>
            <div className="space-y-4">
              {[
                "87% accuracy improvement over single-model evaluation",
                "Real-time performance tracking across all models",
                "Automated failure pattern detection",
              ].map((item, idx) => (
                <div 
                  key={idx} 
                  className="flex items-start gap-3 transition-all duration-300 hover:translate-x-2"
                >
                  <div className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="text-gray-300">{item}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="relative h-[500px]">
            <div className="absolute inset-0 bg-white/5 rounded-2xl border border-white/20 p-8 backdrop-blur-sm">
              <div className="space-y-4">
                {["GPT-4", "Mistral", "Grok"].map((model, idx) => (
                  <div 
                    key={idx}
                    className="p-6 bg-white/5 border border-white/20 rounded-xl transition-all duration-300 hover:bg-white/10"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-sm font-medium text-white">{model}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                        <span className="text-xs text-gray-400">Active</span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs text-gray-400">
                        <span>Accuracy</span>
                        <span className="text-white font-medium">{85 + idx * 5}%</span>
                      </div>
                      <div className="h-3 bg-white/10 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-blue-500 to-green-500 rounded-full transition-all duration-1000 ease-out"
                          style={{ width: `${85 + idx * 5}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Section 2 - Live Refinement */}
      <section id="platform" className="min-h-screen flex items-center px-6 md:px-12 relative bg-zinc-950/50">
        <div className={`max-w-7xl mx-auto grid md:grid-cols-2 gap-16 items-center w-full transition-all duration-1000 ${
          isVisible.feature2 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-20'
        }`}>
          <div className="relative h-[500px] order-2 md:order-1">
            <div className="absolute inset-0 bg-white/5 rounded-2xl border border-white/20 p-8 overflow-hidden backdrop-blur-sm">
              <div className="space-y-3">
                <div className="text-xs uppercase tracking-wider text-gray-400 mb-6">Prompt Evolution</div>
                {[
                  { version: "v1", accuracy: "45%", color: "from-red-500/50 to-red-600/50" },
                  { version: "v2", accuracy: "62%", color: "from-orange-500/50 to-orange-600/50" },
                  { version: "v3", accuracy: "78%", color: "from-yellow-500/50 to-yellow-600/50" },
                  { version: "v4", accuracy: "91%", color: "from-green-500/50 to-green-600/50" },
                ].map((version, idx) => (
                  <div 
                    key={idx}
                    className="flex items-center gap-4 p-4 bg-white/5 border border-white/20 rounded-lg transition-all duration-300 hover:bg-white/10"
                  >
                    <span className="text-sm text-gray-400 w-8">{version.version}</span>
                    <div className="flex-1">
                      <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                        <div 
                          className={`h-full bg-gradient-to-r ${version.color} rounded-full transition-all duration-1000`}
                          style={{ width: version.accuracy }}
                        />
                      </div>
                    </div>
                    <span className="text-sm font-medium text-white w-12 text-right">{version.accuracy}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="order-1 md:order-2">
            <div className="mb-6 text-sm uppercase tracking-wider text-gray-500">Real-Time Evolution</div>
            <h2 className="text-5xl md:text-6xl font-bold mb-6">
              Watch Prompts
              <br />
              Improve
            </h2>
            <p className="text-lg text-gray-400 mb-8 leading-relaxed">
              Live refinement with AI-powered suggestions. Each iteration brings 
              measurable improvements, with full transparency into what changed and why.
            </p>
            <div className="grid grid-cols-2 gap-6">
              {[
                { value: "4.2×", label: "Faster Optimization" },
                { value: "91%", label: "Final Accuracy" },
              ].map((stat, idx) => (
                <div 
                  key={idx} 
                  className="p-6 bg-white/5 rounded-xl border border-white/20 transition-all duration-300 hover:bg-white/10 hover:scale-105"
                >
                  <div className="text-3xl font-bold mb-2">{stat.value}</div>
                  <div className="text-sm text-gray-400">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Feature Section 3 - Dashboard */}
      <section className="min-h-screen flex items-center px-6 md:px-12 relative">
        <div className={`max-w-7xl mx-auto grid md:grid-cols-2 gap-16 items-center w-full transition-all duration-1000 ${
          isVisible.feature3 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-20'
        }`}>
          <div>
            <div className="mb-6 text-sm uppercase tracking-wider text-gray-500">Visual Analytics</div>
            <h2 className="text-5xl md:text-6xl font-bold mb-6">
              Track Every
              <br />
              Metric
            </h2>
            <p className="text-lg text-gray-400 mb-8 leading-relaxed">
              Comprehensive dashboard with pass rates, failure patterns, and 
              improvement trends. All the data you need to make informed decisions.
            </p>
            <div className="space-y-6">
              {[
                { label: "Pass Rate", value: "91%" },
                { label: "Avg Iterations", value: "3.2" },
                { label: "Tokens Saved", value: "12.4K" },
              ].map((metric, idx) => (
                <div 
                  key={idx} 
                  className="flex items-center justify-between pb-4 border-b border-white/20 transition-all duration-300 hover:border-white/40"
                >
                  <span className="text-gray-400">{metric.label}</span>
                  <span className="text-xl font-semibold">{metric.value}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="relative h-[500px]">
            <div className="absolute inset-0 bg-white/5 rounded-2xl border border-white/20 p-8 backdrop-blur-sm">
              <div className="mb-8">
                <div className="text-xs uppercase tracking-wider text-gray-400 mb-2">Performance Overview</div>
              </div>
              <div className="space-y-8">
                {[
                  { label: "Test Case Pass Rate", value: 91, color: "from-green-500 to-emerald-500" },
                  { label: "Model Agreement", value: 87, color: "from-blue-500 to-cyan-500" },
                  { label: "Token Efficiency", value: 94, color: "from-purple-500 to-pink-500" },
                ].map((item, idx) => (
                  <div key={idx}>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm text-gray-400">{item.label}</span>
                      <span className="text-sm font-medium text-white">{item.value}%</span>
                    </div>
                    <div className="h-3 bg-white/10 rounded-full overflow-hidden">
                      <div 
                        className={`h-full bg-gradient-to-r ${item.color} rounded-full transition-all duration-1000 ease-out`}
                        style={{ width: `${item.value}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Integration Section - Oval Pills */}
      <section className="py-32 px-6 md:px-12 border-t border-white/10">
        <div className={`max-w-7xl mx-auto transition-all duration-1000 ${
          isVisible.integration ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-20'
        }`}>
          <div className="text-center mb-16">
            <div className="mb-6 text-sm uppercase tracking-wider text-gray-500">Integrations</div>
            <h2 className="text-4xl md:text-5xl font-bold mb-6">Works with your stack</h2>
            <p className="text-lg text-gray-400">
              Compatible with all major AI frameworks and platforms
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 max-w-3xl mx-auto">
            {[
              "AutoGen",
              "OpenAI",
              "Langchain",
              "Azure AI",
              "Mistral",
              "Anthropic",
            ].map((tech, idx) => (
              <div 
                key={idx}
                className="px-6 py-3 bg-white/5 rounded-full border border-white/20 hover:bg-white/10 hover:border-white/40 transition-all duration-300 hover:scale-110 cursor-pointer"
              >
                <span className="text-sm font-medium text-gray-300 hover:text-white transition-colors duration-300">
                  {tech}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section id="docs" className="py-32 px-6 md:px-12 border-t border-white/10">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-5xl md:text-6xl font-bold mb-6">
            Start building today
          </h2>
          <p className="text-xl text-gray-400 mb-12">
            Join teams using PromptLab to build reliable AI agents
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button className="w-full sm:w-auto px-8 py-4 bg-white text-black font-medium rounded-lg hover:bg-gray-200 transition-all duration-300 hover:scale-105">
              Get Started for Free
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-16 px-6 md:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
            <div className="col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 rounded-lg overflow-hidden">
                  <img src="/PromptLabLogo.jpg" alt="PromptLab" className="w-full h-full object-cover" />
                </div>
                <span className="text-lg font-semibold">PromptLab</span>
              </div>
              <p className="text-sm text-gray-400 max-w-xs">
                AI-powered prompt refinement for reliable agent development
              </p>
            </div>
          </div>
          
          <div className="pt-8 border-t border-white/10 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-400">
              © 2026 PromptLab. All rights reserved.
            </div>
            <div className="flex items-center gap-6">
              {["Twitter", "GitHub", "Discord"].map((social) => (
                <a key={social} href="#" className="text-sm text-gray-400 hover:text-white transition-colors duration-300">
                  {social}
                </a>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}