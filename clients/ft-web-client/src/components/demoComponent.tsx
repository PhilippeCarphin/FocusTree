import * as React from 'react';

interface IProps {
    fmulp: string
    onLaserButtonClick(): any
}

interface IState {
    value: string
}

class DemoComponent extends React.Component<IProps, IState> {
    constructor(props: any){
        super(props);
        this.state = {value: "Enter command"};
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
            </div>
        );
    }
}

export default DemoComponent;
