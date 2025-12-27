import "./styles/App.css";
import ModelBuilder from "./pages/ModelBuilder";

function App() {
  return (
    <div className="app-root">
      <header className="header">
        <h1>ML Model Builder</h1>
        <p>Upload dataset → preprocess → select model → train → view results</p>
      </header>

      <ModelBuilder />
    </div>
  );
}

export default App;
