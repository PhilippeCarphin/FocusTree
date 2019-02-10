import './demoComponent.css'
import JSONTree from 'react-json-tree';
import * as React from 'react';

interface IProps {
    fmulp: string
    onLaserButtonClick(): any
}

interface IState {
    value: string
    tree: object
}

class DemoComponent extends React.Component<IProps, IState> {
    constructor(props: any){
        super(props);
        this.state = {value: "Enter command", tree: {initial: "tree will go here"}};
        fetch('http://localhost:5051/tree', {
            method:'GET',
            headers:{'Content-Type': 'text/plain'}
        }) .then((resp)=> resp.json())
           .then((result)=>{
               this.setState({tree: result});
           });

        this.handleFormChange = this.handleFormChange.bind(this);
        this.handleFormSubmit = this.handleFormSubmit.bind(this);
    }
    private calculateString(){
        return "a member function returned this";
    }

    private handleFormSubmit(event: any){
        event.preventDefault();
        // from https://www.techiediaries.com/react-ajax/
        fetch('http://localhost:5051/send-command', {
            method: 'POST',
            headers: { 'Content-Type': 'text/plain'},
            body: this.state.value
        }).then((resp)=>{
            // console.log(resp.json());
            return resp.json();
        }).then(result => {
            console.log(result);
            if(result.status === "OK"){
                this.setState({"value":""});
            }
        });


        fetch('http://localhost:5051/tree', {
            method:'GET',
            headers:{'Content-Type': 'text/plain'}
        }) .then((resp)=> resp.json())
           .then((result)=>{
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
                <div className="DemoComponent-container">
                    <JSONTree data={this.state.tree}/>
                </div>
            </div>
        );
    }
}

export default DemoComponent;
