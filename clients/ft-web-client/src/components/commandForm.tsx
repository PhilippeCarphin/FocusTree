import * as React from 'react';

interface IProps {
    handleFormSubmit(): any
}
interface IState {
    value: string
}

class CommandForm extends React.Component<IProps, IState>{
    constructor(props: IProps){
        super(props);
        this.state = {value: "Enter command"};
        this.handleFormChange = this.handleFormChange.bind(this);
    }
    private handleFormChange(event: any){
        this.setState({value: event.target.value});
    }

    render(){ return (
        <form onSubmit={this.props.handleFormSubmit}>
            <label>
                Name:
                <input type="text" value={this.state.value} onChange={this.handleFormChange}/>
            </label>
            <input type="submit" value="submit"/>
        </form>
    )};
}

export default CommandForm;
