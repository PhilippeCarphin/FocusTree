import * as React from 'react';

interface IProps {
    fmulp: string
}

class DemoComponent extends React.Component<IProps> {
    public render() {
        return (
            <div>
                <h1>Hello World</h1>
                <p>The value of fmulp is {this.props.fmulp}</p>
            </div>
        );
    }
}

export default DemoComponent;
