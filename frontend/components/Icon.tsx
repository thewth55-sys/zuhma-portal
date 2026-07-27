import { ICONS, type IconName } from "@/lib/nav";

export function Icon({ name, className = "zi" }: { name: IconName; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} dangerouslySetInnerHTML={{ __html: ICONS[name] }} />
  );
}
