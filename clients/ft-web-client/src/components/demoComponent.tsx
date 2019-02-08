import './demoComponent.css'
import * as React from 'react';

interface IProps {
    fmulp: string
    onLaserButtonClick(): any
}

interface IState {
    value: string
    tree?: object
}

class DemoComponent extends React.Component<IProps, IState> {
    constructor(props: any){
        super(props);
        this.state = {value: "Enter command", tree: {initial: "tree will go here"}};
        this.handleFormChange = this.handleFormChange.bind(this);
        this.handleFormSubmit = this.handleFormSubmit.bind(this);
    }
    private calculateString(){
        return "a member function returned this";
    }

    private handleFormSubmit(event: any){
        console.log("Handling submit of form");
        console.log(this.state.value);
        event.preventDefault();
        // from https://www.techiediaries.com/react-ajax/
        fetch('http://localhost:5051/send-command', {
            method: 'POST',
            headers: { 'Content-Type': 'text/plain'},
            body: this.state.value
        }).then((resp)=>{console.log(resp); return resp.json();});


        fetch('http://localhost:5051/tree')
            .then((resp)=> resp.json())
            .then((result)=>{
                console.log(result);
                console.log(JSON.stringify(result, null, 2));
                this.setState({tree: result});
            });

    }

    private handleFormChange(event: any){
        this.setState({value: event.target.value});
        console.log("Handling change of form");
    }

    public render() {
        return (
            <div>
                <h1>Hello World</h1>
                <p>The value of fmulp is {this.props.fmulp}</p>
                <p>{this.calculateString()}</p>
                <button onClick={this.props.onLaserButtonClick}>Activate Lasers</button>
                <form onSubmit={this.handleFormSubmit}>
                    <label>
                        Name:
                        <input type="text" value={this.state.value} onChange={this.handleFormChange}/>
                    </label>
                    <input type="submit" value="submit"/>
                </form>
            <div className="DemoComponent-show-json">
            {
                // L'objectif est juste de voir la string produite par stringify pour qu'elle s'affiche comme dans la console
                JSON.stringify(this.state.tree, null, 2).split("\n").map(
                    (i,key) => <div className="DemoComponent-line" key={key}>{i}</div>
                )

            }
            </div>
            </div>
        );
    }
}

export default DemoComponent;
