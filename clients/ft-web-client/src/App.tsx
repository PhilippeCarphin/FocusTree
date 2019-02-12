import * as React from 'react';
import './App.css';
import DemoComponent from './components/demoComponent'
// import CommandForm from './components/commandForm'

import logo from './logo.svg';

class App extends React.Component {
  public render() {
    return (
      <div className="App">
        <header className="App-header">
          <img src={logo} className="App-logo" alt="logo" />
          <h1 className="App-title">Welcome to FocusTree</h1>
        </header>
        <DemoComponent fmulp="Johnny" onLaserButtonClick={() => console.log("Lasers Activated Callback") } />
      </div>
    );
  }
}

export default App;
