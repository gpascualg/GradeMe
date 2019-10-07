import { Col, Grid } from 'construct-ui';

function color_from_status(status) {
    return 'color-' + ((status) => {
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
    })(status);
}

function color_from_result(score, total, result) {
    return 'color-' + ((score, total, result) => {
        if (typeof score === 'undefined' || typeof total == 'undefined') {
            return 'gray';
        }

        if (!result) {
            return 'red';
        }
        
        return (score < total) ? 'orange' : 'green';
    })(score, total, result);
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

function printable_score(score, def, b, a) {
    if (typeof score === "undefined") {
        return def;
    }

    var score_str = "Tests " + score.absolute.correct + "/" + score.absolute.total + " · Score " +
        score.numeric.score + "/" + score.numeric.total;
        
    if (score.numeric['extra-total'] > 0)
    {
        score_str += " (Extra: " + score.numeric['extra-score'] + "/" + score.numeric['extra-total'] + ")";
    }

    return b + score_str + a;
}

function printable_failure(reason) {
    switch (reason)
    {
        case 'NotImplementedError':
            return 'Function not yet implemented';

        case 'MemoryError':
            return 'Execution ran out of memory';
        
        case 'AssertionError':
            return 'Test failed an assertion';

        case 'GenericError':
            return 'Test failed to execute';

        default:
            return reason;
    }
}

function test_score(score, total) {
    if (typeof score === 'undefined' || typeof total == 'undefined') {
        return '';
    }

    return '[' + score + "/" + total + ']';
}

export default function() {
    var repo = null;
    var instance = null;

    return {
        oninit(vnode) {
            repo = vnode.attrs.repo;
            instance = repo.instances[0]
        },
        view() {
            return [
                <h1 key='h1'>{ repo.org_name + '/' + repo.name }</h1>,
                <h2 key='h2'>{ instance.title }</h2>,
                <h3 key='h3'>
                    [{ printable_users(repo.access_rights) }]
                    <div className={ 'timestamp' }>
                        { printable_date(instance.timestamp) }
                    </div>
                </h3>,
                <Grid key='grid' justify="center">
                    { instance === null || instance.results.length == 0 && <Col span={ 12 }><div className={ 'section-header center' }>There are no tests</div></Col> }
                    { instance.results.map((section) => {
                        return section.type === 0 ? (
                            <Col key={ 'import-error/' + section.module } span={ 12 }>
                                <div className={ 'section-header' } onclick={ (e) => toggle(e, section) }>
                                    { 'Import error: ' + section.module }
                                </div>
                                <Grid className={ 'tests-section' }>
                                    <Col span={ 12 }>
                                        <div className={ 'color-red test-header' }>
                                            <span className={ 'test-name' }>{ section.error }</span>
                                        </div>
                                    </Col>
                                </Grid>
                            </Col>
                        ) : (
                            <Col key={ section.name } span={ 12 }>
                                <div className={ 'section-header' } onclick={ (e) => toggle(e, section) }>
                                    { section.header }
                                    <div className={ 'timestamp' }>
                                        { printable_score(section.score.public, "<hidden>", "[", "]") }
                                    </div>
                                    <div className={ 'timestamp' }>
                                        { printable_score(section.score.private, "", " · [", "]") }
                                    </div>
                                </div>
                                <Grid key={ section.name + '/tests' } className={ 'tests-section' }>
                                    {
                                        section.tests.map((test, i) => {
                                            return <Col key={ section.name + '/tests/' + i } span={ 12 }>
                                                <div className={ color_from_result(test.score, test.max_score, test.result) + ' test-header' }>
                                                    <span className={ 'test-name bold' }>{ test.name }</span>
                                                    { test.desc && <span> - { test.desc }</span> }
                                                    <div className={ 'timestamp' }>
                                                        { test_score(test.score, test.max_score) }
                                                    </div>
                                                </div>
                                                { (!test.result || (test.score != test.max_score)) && 
                                                    <div className={ 'inner-test' }>
                                                        { test.details != 'None' && 
                                                            <div className={ 'test-details' }>{ test.details }</div> 
                                                        }
                                                        { !test.result &&
                                                            <div className={ 'test-failure' }>{ printable_failure(test.failure_reason) }</div>
                                                        }
                                                        { test.failure_reason != 'NotImplementedError' && 
                                                            <div className={ 'test-hint' }>{ test.hint }</div> 
                                                        }
                                                    </div> 
                                                }
                                            </Col>
                                        })
                                    }
                                </Grid>
                            </Col>
                        );
                    }) }
                </Grid>,
            ];
        },
    };
}
