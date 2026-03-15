/** Small shared utility helpers */

export function randomSessionId(): string {
  return Math.random().toString(36).slice(2, 11);
}
