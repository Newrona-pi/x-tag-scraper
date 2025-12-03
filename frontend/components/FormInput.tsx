"use client";

interface FormInputProps {
  label: string;
  type: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
  min?: string;
  max?: string;
  prefix?: string;
}

export default function FormInput({
  label,
  type,
  value,
  onChange,
  placeholder,
  required = false,
  min,
  max,
  prefix,
}: FormInputProps) {
  return (
    <div className="w-full">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {prefix ? (
        <div className="flex items-center">
          <span className="inline-flex items-center px-4 py-2 border border-r-0 border-gray-300 bg-gray-50 text-gray-700 rounded-l-lg font-medium">
            {prefix}
          </span>
          <input
            type={type}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            required={required}
            min={min}
            max={max}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-r-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
          />
        </div>
      ) : (
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          required={required}
          min={min}
          max={max}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
        />
      )}
    </div>
  );
}

