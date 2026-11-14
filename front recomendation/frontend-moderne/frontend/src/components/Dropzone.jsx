import { UploadCloud } from "lucide-react";
import { useRef, useState } from "react";

export default function Dropzone({ multiple = false, onFiles, label, hint, children, compact = false }) {
  const [over, setOver] = useState(false);
  const inputRef = useRef(null);

  const take = (list) => {
    const files = Array.from(list || []).filter((file) => file.type.startsWith("image/"));
    if (files.length) onFiles(multiple ? files : files.slice(0, 1));
  };

  return (
    <div
      className={`dropzone${over ? " is-over" : ""}${compact ? " is-compact" : ""}`}
      onClick={() => inputRef.current?.click()}
      onDragLeave={() => setOver(false)}
      onDragOver={(event) => {
        event.preventDefault();
        setOver(true);
      }}
      onDrop={(event) => {
        event.preventDefault();
        setOver(false);
        take(event.dataTransfer.files);
      }}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          inputRef.current?.click();
        }
      }}
      role="button"
      tabIndex={0}
    >
      <input
        accept="image/*"
        hidden
        multiple={multiple}
        onChange={(event) => {
          take(event.target.files);
          event.target.value = "";
        }}
        ref={inputRef}
        type="file"
      />
      {children ?? (
        <>
          <span className="dropzone-icon">
            <UploadCloud size={22} />
          </span>
          <strong>{label}</strong>
          {hint && <span className="muted">{hint}</span>}
        </>
      )}
    </div>
  );
}
