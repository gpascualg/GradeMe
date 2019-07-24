import { Col, Grid } from 'construct-ui';

export default function() {
    var instances = [];

    return {
        oninit(vnode) {
            instances = vnode.attrs.instances;
        },
        view() {
            return [
                <h1 key='h1'>Tests: </h1>,
                <Grid key='grid' justify="center">
                    { instances.map((ist) => {
                        return <Col key={ ist.id } span={ 12 }>
                            <div className={ 'color-' + ist.color }>{ ist.name }</div>
                        </Col>;
                    }) }
                </Grid>,
            ];
        },
    };
}