import { useRef, useState } from "react";

interface FileUploadProps {
  file: File | null;
  onFileSelected: (file: File | null) => void;
  error?: string;
}

const VALID_EXT = [".xlsx", ".xls"];

function isValidExcel(file: File): boolean {
  const name = file.name.toLowerCase();
  return VALID_EXT.some((ext) => name.endsWith(ext));
}

export default function FileUpload({
  file,
  onFileSelected,
  error,
}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  function handleFiles(files: FileList | null) {
    setLocalError(null);
    if (!files || files.length === 0) return;
    const f = files[0];
    if (!isValidExcel(f)) {
      setLocalError("El archivo debe ser un Excel (.xlsx o .xls).");
      onFileSelected(null);
      return;
    }
    onFileSelected(f);
  }

  const shownError = localError ?? error;

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        className={[
          "flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition",
          dragging
            ? "border-brand-600 bg-brand-50"
            : "border-slate-300 bg-slate-50 hover:border-brand-600 hover:bg-brand-50",
        ].join(" ")}
      >
        <svg
          className="mb-3 h-10 w-10 text-brand-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
          />
        </svg>
        <p className="font-medium text-slate-700">
          Arrastra el Excel aquí o haz clic para seleccionarlo
        </p>
        <p className="mt-1 text-sm text-slate-500">
          Solo se aceptan archivos .xlsx y .xls
        </p>

        <input
          ref={inputRef}
          type="file"
          accept=".xlsx,.xls"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {file && (
        <div className="mt-3 flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-2.5">
          <div className="flex items-center gap-2 text-sm text-slate-700">
            <span className="inline-flex h-7 w-7 items-center justify-center rounded bg-green-100 text-green-700">
              ✓
            </span>
            <span className="font-medium">{file.name}</span>
            <span className="text-slate-400">
              ({(file.size / 1024).toFixed(0)} KB)
            </span>
          </div>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onFileSelected(null);
              if (inputRef.current) inputRef.current.value = "";
            }}
            className="text-sm font-medium text-slate-500 hover:text-red-600"
          >
            Quitar
          </button>
        </div>
      )}

      {shownError && (
        <p className="mt-2 text-sm font-medium text-red-600">{shownError}</p>
      )}
    </div>
  );
}
