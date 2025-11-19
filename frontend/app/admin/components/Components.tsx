"use client";
import React, { useEffect, useRef, useState } from "react";

type SummaryCardProps = {
  value: number | string;
  description: string;
  type?: "number" | "percent";
  color?: string;
};

export function SummaryCard({ value, description, type = "number" }: SummaryCardProps) {
  return (
    <div className="h-full w-[40%] shrink-0 rounded-md bg-primary flex flex-col justify-center items-center p-4">
      {type === "percent" ? (
        <h4 className="text-4xl md:text-6xl font-bold">{value}%</h4>
      ) : (
        <h4 className="text-4xl md:text-6xl font-bold">{value}</h4>
      )}
      <h3 className="mt-2 text-sm text-primary">{description}</h3>
    </div>
  );
}

type SelectOption = string | { label: string; value: any };

type CustomSelectProps = {
  value?: string;
  widthClass?: string; // tailwind width class like 'w-20' or custom
  options: SelectOption[];
  onChange: (value: any) => void;
  className?: string;
  buttonClassName?: string;
  dropdownClassName?: string;
  placeholder?: string;
};

export function CustomSelect({
  value,
  widthClass = "w-40",
  options,
  onChange,
  className = "",
  buttonClassName = "",
  dropdownClassName = "",
  placeholder = "Select...",
}: CustomSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setIsOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className={`relative ${className}`} ref={ref}>
      <button
        onClick={() => setIsOpen((s) => !s)}
        className={`z-20 ${widthClass} p-1 text-left ${isOpen ? "rounded-t-sm shadow" : "rounded-sm"} bg-gray-300/70 ${buttonClassName}`}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        {value ?? placeholder}
      </button>

      {isOpen && (
          <div className={`z-10 absolute overflow-hidden ${widthClass} bg-primary/70 backdrop-blur-md rounded-b-sm shadow ${dropdownClassName}`} role="listbox">
          {options.map((opt) => {
            const key = typeof opt === "string" ? opt : String(opt.value);
            const label = typeof opt === "string" ? opt : opt.label;
            const val = typeof opt === "string" ? opt : opt.value;
            return (
              <div
                key={key}
                  className="p-1 hover:bg-secondary/50 cursor-pointer"
                onClick={() => {
                  onChange(val);
                  setIsOpen(false);
                }}
                role="option"
              >
                {label}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

type ButtonOption = { label: string; value: string };

type ButtonGroupProps = {
  options: ButtonOption[];
  selected: string;
  onSelect: (value: string) => void;
  className?: string;
};

export function ButtonGroup({ options, selected, onSelect, className = "" }: ButtonGroupProps) {
  return (
    <div className={`flex rounded-sm overflow-hidden ${className}`} role="group">
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => onSelect(option.value)}
          type="button"
          className={`px-3 py-1 text-sm font-medium transition-colors ${
              selected === option.value ? "bg-secondary/60" : "bg-secondary text-primary hover:bg-secondary/40"
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

