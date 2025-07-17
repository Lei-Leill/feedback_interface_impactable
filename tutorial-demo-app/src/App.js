import logo from './logo.svg';
import './App.css';
import React  from 'react';

function App() {
  const handleClick = () => {
    alert('You clicked the button!');
  };

  return (
    <button onClick={handleClick}>
      Click Me
    </button>
  );
  // return (
  //   <div className="App">
  //     <h1>Hello World</h1>
  //     {/* <header className="App-header">
  //       <img src={logo} className="App-logo" alt="logo" />
  //       <p>
  //         Edit <code>src/App.js</code> and save to reload.
  //       </p>
  //       <a
  //         className="App-link"
  //         href="https://reactjs.org"
  //         target="_blank"
  //         rel="noopener noreferrer"
  //       >
  //         Learn React
  //       </a>
  //     </header> */}
  //   </div>
  // );

}

export default App;
