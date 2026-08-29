import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// 片段相关度（重排概率 0~1）分档着色：高 ≥0.7 青绿 / 中 0.3~0.7 琥珀 / 低 <0.3 灰
export function relevanceScoreStyle(score: number): string {
  if (score >= 0.7) return "text-[#0d9488]"
  if (score >= 0.3) return "text-amber-600"
  return "text-slate-400"
}
