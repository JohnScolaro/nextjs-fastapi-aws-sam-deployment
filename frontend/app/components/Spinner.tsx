export default function Spinner() {
    return (
      <div className="spinner">
        <style jsx>{`
          .spinner {
            width: 20px;
            height: 20px;
            border: 3px solid #ccc;
            border-top: 3px solid black;
            border-radius: 50%;
            animation: spin 1s linear infinite;
          }
  
          @keyframes spin {
            from {
              transform: rotate(0deg);
            }
            to {
              transform: rotate(360deg);
            }
          }
        `}</style>
      </div>
    );
  }
  