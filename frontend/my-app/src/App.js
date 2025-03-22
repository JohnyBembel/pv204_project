import logo from './logo.svg';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          Ayou lighting network test!!
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
        <br />
        <br />
        <br />
        <button
            onClick={() => {
              // OpenNode payment request logic here
              console.log('OpenNode payment button clicked');
            }}
          >
            Pay with OpenNode
          </button>
      </header>
    </div>
  );
}

export default App;
