import * as React from 'react';

interface IProps {
    fmulp: string
    onLaserButtonClick(): any
}

class DemoComponent extends React.Component<IProps> {
    private calculateString(){
        return "a member function returned this";
    }

    public render() {
        return (
            <div>
                <h1>Hello World</h1>
                <p>The value of fmulp is {this.props.fmulp}</p>
                <p>{this.calculateString()}</p>
                <button onClick={this.props.onLaserButtonClick}>Activate Lasers</button>
            </div>
        );
    }
}

export default DemoComponent;
