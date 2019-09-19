import { Col, Grid } from 'construct-ui';

function color_from_status(status) {
    switch (status) {
        // Fatal cases
        case 'checksum-mismatch':
            return 'red';
        case 'execution-error':
            return 'red';
        case 'missing-yml':
            return 'red';
        case 'unkown-error':
            return 'red';

        // Skipped cases
        case 'branch-mismatch':
            return 'orange';

        // Success
        case 'done':
            return 'green';

        // Unkown
        default:
            return 'red';
    }
}

function printable_date(timestamp) {
    var date = new Date(timestamp * 1000);
    
    var hours = "0" + date.getHours();
    var minutes = "0" + date.getMinutes();
    var day = "0" + date.getDay();
    var month = "0" + date.getMonth();
    var year = date.getFullYear();

    return day.substr(-2) + "/" + month.substr(-2) + "/" + year + " " +
         hours.substr(-2) + ":" + minutes.substr(-2);
}

export default function() {
    var repos = [];

    return {
        oninit(vnode) {
            repos = vnode.attrs.repos;
        },
        view() {
            return [
                <h1 key='h1'>Tests: </h1>,
                <Grid key='grid' justify="center">
                    { repos.map((repo) => {
                        return <Col key={ repo.org_name + '/' + repo.name } span={ 12 }>
                            <div className={ 'color-repo' }>{ repo.org_name }/{ repo.name }</div>
                            <Grid key={ repo.org_name + '/' + repo.name + '/instances' }>
                                {
                                    repo.instances.map((ist) => {
                                        return <Col key={ ist.hash } span={ 12 }>
                                            <div className={ color_from_status(ist.status) }>
                                                { ist.title }
                                                <div className={ 'timestamp' }>
                                                    { printable_date(ist.timestamp) }
                                                </div>
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
