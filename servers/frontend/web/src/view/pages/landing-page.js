import { Col, Grid, Input, Icon, Icons } from 'construct-ui';
import { route } from '../components/helper';
import { db, upsert } from '../../database';

function color_from_status(status) {
    return 'color-' + ((status) => {
        switch (status) {
            // Fatal cases
            case 'checksum-mismatch':
            case 'execution-error':
            case 'missing-yml':
            case 'unkown-error':
                return 'red';

            // Skipped cases
            case 'pending':
            case 'branch-mismatch':
                return 'orange';

            // Success
            case 'done':
                return 'green';

            // Unkown
            default:
                return 'red';
        }
    })(status);
}

function is_failed(status) {
    return color_from_status(status) != 'color-green';
}

function printable_date(timestamp) {
    var date = new Date(timestamp * 1000);
    
    var hours = "0" + date.getHours();
    var minutes = "0" + date.getMinutes();
    var day = "0" + date.getDate();
    var month = "0" + date.getMonth();
    var year = date.getFullYear();

    return day.substr(-2) + "/" + month.substr(-2) + "/" + year + " " +
         hours.substr(-2) + ":" + minutes.substr(-2);
}

function toggle(e, repo)
{
    if (repo.height == '0') {
        repo.height = '1000px';
    }
    else {
        repo.height = '0';
    }
}

function printable_users(access_rights) {
    var users = []
    for (var i = 0; i < access_rights.length; ++i)
    {
        if (access_rights[i]['permission'] == 'member') {
            users.push(access_rights[i]['name']);
        }
    }

    return users.join(', ');
}

function setroute(e, repo, ist) {
    route('/results/' + repo.id.org + '/' + repo.id.repo + '/' + ist.branch + '/' + ist.hash);
}

function search(e) {
    var search = e.srcElement.value;

    upsert(db, 'data', {key: 'search'}, {key: 'search', value: search})
        .then(() => route('/index'));

    return search;
}

export default function() {
    var repos = [];
    var user = undefined;
    var config = undefined;

    return {
        oninit(vnode) {
            repos = vnode.attrs.repos;
            user = vnode.attrs.user;
            config = vnode.attrs.config;
        },
        view() {
            return [
                <div key='header'>
                    <h1 key='h1'>Tests</h1>
                    {
                        user.is_admin && <div class='search-div'>
                            <Input 
                                placeholder={ 'Username or niub' }
                                size='lg'
                                fluid={ true }
                                contentRight={ <Icon name={ Icons.SEARCH } size='lg' onclick={ (e) => config.search = search(e) }></Icon> }
                                onchange={ (e) => config.search = search(e) }
                                value={ config.search || '' }
                            ></Input>
                        </div>
                    }
                </div>,
                <Grid key='grid' justify="center">
                    { repos.length == 0 && <Col span={ 12 }><div className={ 'section-header center' }>There are no tests</div></Col> }
                    { repos.map((repo) => {
                        return <Col key={ repo.org_name + '/' + repo.name } span={ 12 }>
                            <div className={ 'color-repo' } onclick={ ((repo) => (e) => toggle(e, repo))(repo) }>
                                { repo.org_name }/{ repo.name }
                                <div className={ 'timestamp' }>
                                    [{ printable_users(repo.access_rights) }]
                                </div>
                            </div>
                            <Grid key={ repo.org_name + '/' + repo.name + '/instances' } style={ { 'max-height': repo.height || '1000px' } }>
                                {
                                    repo.instances.map((ist) => {
                                        return <Col key={ ist.branch + '/' + ist.hash } span={ 12 }>
                                            <div className={ color_from_status(ist.status) } onclick={ ((repo, ist) => (e) => setroute(e, repo, ist))(repo, ist) }>
                                                { !is_failed(ist.status) && 
                                                    <span className={ 'bold' }>[{ ist.score }/{ ist.total }] </span>
                                                }

                                                { ist.title }
                                                <div className={ 'timestamp' }>
                                                    { printable_date(ist.timestamp) }
                                                </div>
                                                { is_failed(ist.status) &&
                                                    <div className='pad-left'>Failure reason: <span className={ 'capitalize' }>{ ist.status.split('-').join(' ') }</span></div>
                                                }
                                            </div>
                                        </Col>
                                    })
                                }
                            </Grid>
                        </Col>;
                    }) }
                </Grid>,
            ];
        },
    };
}
