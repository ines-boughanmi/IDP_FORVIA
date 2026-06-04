export function SearchInput({ value, onChange, placeholder = 'Search' }: { value: string; onChange: (value: string) => void; placeholder?: string }) {
  return <input className="input" value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />;
}
