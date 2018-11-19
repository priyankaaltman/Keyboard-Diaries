
'use strict';

class ContactsList extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            contacts: [],
        };
    }

    componentDidMount() {
        console.log("component did mount")
        fetch('/api/contacts')
            .then(response => response.json())
            .then(data => this.setState( { contacts: data.contacts } ))
    }

    render(){
        return (
            <div>
                {this.state.contacts.map(function(contact) {
                    return( 
                        <li key={contact.id}>
                            <a href={"/contacts/" + contact.id}>{contact.name}</a>
                        </li>
                    );
                })}
            </div>
        )
    }
}

ReactDOM.render(<ContactsList />, document.getElementById('contacts_list'))
