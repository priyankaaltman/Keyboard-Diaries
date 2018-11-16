'use strict';
// import DatePicker from "react-datepicker";
// import moment from "moment";
// import "react-datepicker/dist/react-datepicker.css"

class App extends React.Component {

    constructor(props){
        super(props);
        this.state = {
            start_date: '',
            end_date: '',
            keyword: ''
        };
    }

    handleGeneralSearch(event, start_date, end_date, keyword) {
        event.preventDefault();

        fetch('/api/general-search', {start_date, end_date, keyword})
            .then(response => response.text())
            .then(data => console.log(data));
    }

    render() {
        return (
          <div className="App">
            <Navbar/>
            <Sidebar/>
            <Body onGeneralSearch = {(event, start_date, end_date, keyword) => this.handleGeneralSearch(event, start_date, end_date, keyword)}/>
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
                <GeneralSearch handleSubmit={this.props.onGeneralSearch}/>
                <Folders />

            </div>
        )
    }
}

class OnThisDay extends React.Component {
    
    constructor(props) {
        super(props);

        this.state = {
            friends: [],
        };
    }

    componentDidMount() {
        fetch('/api/one-year-ago-today')
            .then(response => response.json())
            .then(data => this.setState( { friends: data.friends } ))
    }
    
    render(){
        return (
            <div className="bodysection">
                <h2>On This Day</h2>
                <div>
                    {this.state.friends.map(function(object) {
                        return(
                            <li key={object.id}>See conversation with {object.name}</li>
                        );
                    })}
                </div>
            </div>
        );
    }
}

class GeneralSearch extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            'start_date': '',
            'end_date': '',
            'keyword': '',
            'messages': []
        }

        this.onChange = this.onChange.bind(this)
    }

    onChange(event) {
        this.setState ({ [event.target.name]: event.target.value });
    }


    render() {
        const {start_date, end_date, keyword} = this.state;
        return (
            <div className="bodysection">
                <h2>General Search</h2>
                <form
                    onSubmit={(event) => this.props.handleSubmit(event, start_date, end_date,keyword)}
                >
                    <label>Start Date (MM-DD-YYYY): 
                        <input type="text" name="start_date" value={this.state.start_date} onChange={this.onChange}/>
                    </label>
                    <label>End Date (MM-DD-YYYY): 
                        <input type="text" name="end_date" value={this.state.end_date} onChange={this.onChange}/></label>
                    <label>Keyword: 
                        <input type="text" name="keyword" keyword={this.state.keyword} onChange={this.onChange}/></label>
                    <input type="submit" />
                </form>
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
            <div className="bodysection">
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









