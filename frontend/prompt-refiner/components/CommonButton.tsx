"use client";

import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variants?: "primary" | "secondary";
    children: React.ReactNode;
}

export default function CommonButton({ variant = "primary", children, className = "", ...props }: ButtonProps) {
    const baseStyles = "px-6 py-2 text-sm font-medium rounded-lg transition-all duration-300 transform active:scale-95";
  
  const variants = {
    primary: "bg-white text-black hover:bg-gray-200 hover:scale-105",
    secondary: "bg-white/5 text-white border border-white/20 hover:bg-white/10 hover:border-white/40"
  };

  return (
    <button 
      className={`${baseStyles} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}