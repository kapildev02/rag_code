import React, { useState } from "react";

export type FormErrors<T> = {
  [key in keyof T]?: string;
};

const useFormValidation = <T extends Record<string, any>>(
  initialValues: T,
  validate: (values: T) => FormErrors<T>,
) => {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<FormErrors<T>>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement> | React.ChangeEvent<HTMLSelectElement>) => {
    // eslint-disable-next-line no-unsafe-optional-chaining
    const { name, value, dataset } = e?.target;

    const regexPattern = dataset?.regex ? new RegExp(dataset.regex) : null;

    // const trimmedValue = value.trim().replace(/\s+/g, " ");
    const trimmedValue = value.trim().replace(/\s+/g, "");

    if (regexPattern) {
      if (regexPattern.test(trimmedValue)) {
        setValues((prev: T) => ({ ...prev, [name]: trimmedValue }));
      }
    } else {
      setValues((prev: T) => ({ ...prev, [name]: trimmedValue }));
    }
    setErrors({});
  };

  const onValidate = (): boolean => {
    const newErrors = validate(values);
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (callback: () => void) => {
    if (onValidate()) {
      callback();
    }
  };

  const onReset = () => {
	setValues(initialValues);	
	setErrors({});
  }

  return { values, errors, handleChange, handleSubmit, setErrors, setValues, onReset };
};

export default useFormValidation;