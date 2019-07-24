import { Button, Icons } from 'construct-ui';

export default function() {

    return {
        oninit(/* vnode */) {
        },
        view() {
            return (
                <div className="d-flex flex-wrap justify-content-center">
                    <Button iconLeft={ Icons.USER } intent='primary' label='Login with Github' 
                        size='xl' fluid onclick={ () => location.href = '/login' } />
                </div>
            );
        },
    };
}