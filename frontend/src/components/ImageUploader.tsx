import { useRef, useState } from 'react'

interface Props {
  onUpload: (file: File) => void
  disabled: boolean
}

export default function ImageUploader({ onUpload, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [preview, setPreview] = useState<string | null>(null)

  function handleFile(file: File) {
    setPreview(URL.createObjectURL(file))
    onUpload(file)
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`relative border-2 border-dashed rounded-xl flex flex-col items-center justify-center cursor-pointer transition-colors
        ${disabled ? 'opacity-50 cursor-not-allowed border-gray-700' : 'border-gray-600 hover:border-indigo-500'}
        ${preview ? 'h-64' : 'h-48'}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleChange}
        disabled={disabled}
      />
      {preview ? (
        <img src={preview} alt="preview" className="h-full w-full object-contain rounded-xl" />
      ) : (
        <div className="text-center text-gray-500 select-none">
          <p className="text-4xl mb-2">+</p>
          <p className="text-sm">Drop an image or click to upload</p>
        </div>
      )}
    </div>
  )
}
