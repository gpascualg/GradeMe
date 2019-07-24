import './styles.scss';
import 'bootstrap/dist/css/bootstrap.min.css';
import classNames from 'classnames';
import { onEndTransition, route } from '../helper';

/**
 * A component that wraps another component with some common
 * page layout markup and styles.
 */
export default function() {
    var isMenuOpen = false;
    var isTransitionInCourse = false;
    
    function handleMenu()
    {
        isMenuOpen = !isMenuOpen;

        if (isMenuOpen)
        {
            isTransitionInCourse = true;
        }
            
        let page = document.getElementsByClassName('page')[0];
        if (isMenuOpen) {
            page.style.transform = 'translate3d(0, 30vh, ' + parseInt(-100) + 'px)';
        }
        else {
            page.style.transform = 'translate3d(0, 0, 0)';
        }

        onEndTransition(page, function() {
            isTransitionInCourse = isMenuOpen;
        });
    }
    
    function openPage(e)
    {
        handleMenu();

        let targetPage = e.target.getAttribute('href');
        if (targetPage != m.route.get())
        {
            route(targetPage);
        }

        e.preventDefault();
    }

    function closeMenu(e)
    {
        if (!isMenuOpen)
        {
            e.redraw = false;
            return;
        }

        handleMenu();
    }

    return {
        view(vnode) {
            return [
                <nav className={ classNames({'pages-nav': true, 'pages-nav--open': isMenuOpen}) } key='nav'>
                    <div className="pages-nav__item"><a className="link link--page" href="/index" onclick={ (e) => openPage(e) }>Home</a></div>
                    <div className="pages-nav__item"><a className="link link--page" href="/admin" onclick={ (e) => openPage(e) }>Admin</a></div>
                    <div className="pages-nav__item"><a className="link link--page" href="/changelog" onclick={ (e) => openPage(e) }>Changelog</a></div>
                </nav>,

                <div className={ classNames({'pages-stack': true, 'pages-stack--open': isTransitionInCourse}) } key='pages-stack'>
                    <div
                        className={ classNames({'page': true, 'page--selectable': isMenuOpen}) }
                        onclick={ (e) => closeMenu(e) }
                        id="page-home" 
                        style='translate3d(0, 0, 0)'>

                        <div className='container'>
                            { vnode.children }
                        </div>
                    </div>
                </div>,
                
                <button className={ classNames({'menu-button': true, 'menu-button--open': isMenuOpen }) } key='menu' onclick={ () => handleMenu() }>
                    <span>Menu</span>
                </button>,
            ];
        },
    };
}
