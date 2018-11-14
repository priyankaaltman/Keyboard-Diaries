'use strict';

class App extends React.Component {
    render() {
        return (
          <div className="App">
            <Navbar/>
            <Sidebar/>
            <Body/>
          </div>
        )
    }
}

class Navbar extends React.Component {
    render() {
        return (
            <div className="Navbar">
                <HomeButton/>
                <UploadButton/>
                <LogInOrOutButton/>
            </div>
        )
    }
}

// class Sidebar extends React.Component {
//     render() {
//         return (
//             <div className="Sidebar">
//                 <Groups />
//                 <Contacts />
//             </div>
//         )
//     }
// }

class Body extends React.Component {
    render() {
        return (
            <div className="Body" />
        )
    }
}

class HomeButton extends React.Component {
    render () {
        return (
            <a href="/">Home</a>
        )
    }
}

// const e = React.createElement;

class LogInOrOutButton extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            text: "Log In",
            link: "/login"
        };
    }

    changeTextAndLink() {
        if (this.state.text === "Log In"){
            return this.setState({ text: "Log Out", link: "/logout" })
        } else{
            return this.setState({ text: "Log In", link: "/login" })
        }
    }

    render () {

        return (
            <a href={this.state.link} onClick={this.changeTextAndLink}>
                {this.state.text}
            </a>
        )
    }
}


//         return e(
//             'button',
//             { onClick: () => this.setState ({ text: "Log Out", link:"/logout" }) },
//             <a href={this.state.link}>{this.state.text}</a>
//         );
//     }
        
// }

class UploadButton extends React.Component {
     render () {
        return (
            <a href="/upload">Upload</a>
        )
    }
}








