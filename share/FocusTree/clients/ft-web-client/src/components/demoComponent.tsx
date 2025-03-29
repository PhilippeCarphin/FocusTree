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
    termOutput: string
    errOutput: string
}

const url_prefix = (
    process.env.NODE_ENV === "development"
    ? 'http://localhost:5051'
    : ''
);

class DemoComponent extends React.Component<IProps, IState> {
    constructor(props: any){
        super(props);
        this.state = {value: "current", tree: {}, termOutput: "", errOutput: "ERROR : Probably couldn't connect to a server"};

        this.fetchTree().then((result)=> this.setState({tree: result['root_nodes'], errOutput: ""}));
        this.sendCommand('current').then((result) => {this.setState({termOutput: result.term_output})});

        this.handleFormChange = this.handleFormChange.bind(this);
        this.handleFormSubmit = this.handleFormSubmit.bind(this);
    }

    private async sendCommand(command: string) {
        const resp = await fetch(url_prefix + '/api/send-command', {
            method: 'POST',
            headers: {'Content-Type': 'text/plain'},
            body: command
        });
        // console.log(resp.json());
        return resp.json();
    }

    private fetchTree(){
        return fetch(url_prefix + '/api/tree', {
            method:'GET',
            headers:{'Content-Type': 'text/plain'}
        }) .then((resp)=> resp.json())
    }

    private handleFormSubmit(event: any){
        event.preventDefault();
        // from https://www.techiediaries.com/react-ajax/
        this.sendCommand(this.state.value).then(result => {
            console.log(result);
            if(result.status === "OK"){
                let to = result['term_output'];
                // to = to.replace('\n', 'ASDF<br>');
                let ti = to.split('\n').map((i:any, key:any) => <div key={key}>{i}</div>);
                this.setState({value:"", termOutput: ti , errOutput: ""});
            } else {
                this.setState({errOutput: result.error})
            }

        }).then(()=>this.fetchTree());
    }

    private handleFormChange(event: any){
        this.setState({value: event.target.value});
        console.log("Handling change of form");
    }

    public render() {
        return (
            <div>
                <div className="DemoComponent-code" >
                    <code className="DemoComponent-code">
                        {this.state.termOutput}
                    </code>
                </div>
                <div className="DemoComponent-error">
                    <code className="DemoComponent-error">
                        {this.state.errOutput}
                    </code>
                </div>
                <form onSubmit={this.handleFormSubmit}>
                    <label>
                        Enter command:
                        <input type="text" value={this.state.value} onChange={this.handleFormChange}/>
                    </label>
                    <input type="submit" value="submit"/>
                </form>
                <a href="/help.html">Click Here for help</a>
                <div className="DemoComponent-container">
                    <JSONTree data={this.state.tree}/>
                </div>
            </div>
        );
    }
}

export default DemoComponent;
