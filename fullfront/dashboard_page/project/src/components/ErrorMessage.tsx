import React from 'react'

interface ErrorMessageProps {
  message: string
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ message }) => {
  return (
    <div
      style={{
        backgroundColor: '#fff5f5',
        border: '1px solid #fc8181',
        borderRadius: '8px',
        padding: '16px',
        color: '#c53030',
        marginBottom: '16px',
      }}
    >
      {message}
    </div>
  )
}

export default ErrorMessage
