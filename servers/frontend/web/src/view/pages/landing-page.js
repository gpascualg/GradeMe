import { Col, Grid } from 'construct-ui';

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
                            <div className={ 'color-gray' }>{ repo.org_name }/{ repo.name }</div>
                            <Grid key={ repo.org_name + '/' + repo.name + '/instances' }>
                                {
                                    repo.instances.map((ist) => {
                                        return <Col key={ ist.hash } span={ 10 }>
                                            <div className={ 'color-green' }>{ ist.title } ({ ist.status })</div>
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
