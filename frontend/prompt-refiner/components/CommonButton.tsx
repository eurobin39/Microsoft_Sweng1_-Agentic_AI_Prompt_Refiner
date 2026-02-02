"use client";

import React from "react";

// 1. Define the specific variants allowed
type ButtonVariant = "primary" | "secondary";

// 2. Extend standard HTML button props with our custom variant
interface CommonButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  children: React.ReactNode;
}

export default function CommonButton({ 
  variant = "primary", 
  children, 
  className = "", 
  ...props 
}: CommonButtonProps) {
  
  const baseStyles = "px-6 py-2 text-sm font-medium rounded-lg transition-all duration-300 transform active:scale-95";
  
  // 3. Explicitly type the styles object to prevent the "any" error
  const variantStyles: Record<ButtonVariant, string> = {
    primary: "bg-white text-black hover:bg-gray-200 hover:scale-105",
    secondary: "bg-white/5 text-white border border-white/20 hover:bg-white/10 hover:border-white/40"
  };

  return (
    <button 
      className={`${baseStyles} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}