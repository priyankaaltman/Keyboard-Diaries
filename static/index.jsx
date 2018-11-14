'use strict';


class App extends React.Component {
    render() {
        return (
          <div className="App">
            <Navbar/>
            <Sidebar/>
            <Body />
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

class HomeButton extends React.Component {
    render () {
        return (
            <a href="/" className="navbutton">Home</a>
        )
    }
}

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
            <a href={this.state.link} onClick={this.changeTextAndLink} className="navbutton">
                {this.state.text}
            </a>
        )
    }
}

class UploadButton extends React.Component {
     render () {
        return (
            <a href="/upload" className="navbutton">Upload</a>
        )
    }
}

class Sidebar extends React.Component {
    render() {
        return (
            <div className="Sidebar">
                <Groups />
                <Contacts/>
            </div>
        )
    }
}

class Contacts extends React.Component { 

    constructor(props) {
        super(props);

        this.state = {
            data: [],
        };
    }

    componentDidMount() {
        fetch('/api/contacts')
            .then(response => response.json())
            .then(data => this.setState( { data: data.contacts } ))
    }
    
    render(){
        return (
            <div className="sidebarsection">
                <h2>Contacts</h2>
                <div>
                    {this.state.data.map(function(object) {
                        return(
                            <li key={object.id}>{object.name}</li>
                        );
                    })}
                </div>
            </div>
        );
    }
}

class Groups extends React.Component { 

    constructor(props) {
        super(props);

        this.state = {
            data: [],
        };
    }

    componentDidMount() {
        fetch('/api/groups')
            .then(response => response.json())
            .then(data => this.setState( { data: data.groups } ))
    }
    
    render(){
        return (
            <div className="sidebarsection">
                <h2>Groups</h2>
                <div>
                    {this.state.data.map(function(object) {
                        return(
                            <li key={object.id}>{object.title}</li>
                        );
                    })}
                </div>
            </div>
        );
    }
}

class Body extends React.Component {
    render() {
        return (
            <div className="Body">
                <OnThisDay />
                <GeneralSearch />
                <Folders />
            </div>
        )
    }
}

class OnThisDay extends React.Component {
    render() {
        return (
            <div className="bodysection">
            </div>
        )
    }
}

class GeneralSearch extends React.Component {
    render() {
        return (
            <div className="bodysection">
            </div>
        )
    }
}

class Folders extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            data: [],
        };
    }

    componentDidMount() {
        fetch('/api/folders')
            .then(response => response.json())
            .then(data => this.setState( { data: data.folders } ))
    }
    
    render(){
        return (
            <div className="bodybarsection">
                <h2>Folders</h2>
                <div>
                    {this.state.data.map(function(object) {
                        return(
                            <li key={object.id}>{object.title}</li>
                        );
                    })}
                </div>
            </div>
        );
    }
}









