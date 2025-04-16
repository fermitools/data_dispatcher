::: {.related role="navigation" aria-label="Related"}
### Navigation

-   [index](genindex.html "General Index")
-   [next](worker.html "File Processing with Data Dispatcher") \|
-   [previous](ui.html "Data Dispatcher User Interface") \|
-   [Data Dispatcher documentation](index.html) »
-   [Python API]()
:::

::: document
::: documentwrapper
::: bodywrapper
::: {.body role="main"}
::: {#python-api .section}
# Python API[¶](#python-api "Link to this heading"){.headerlink}

Python API is the recommended way for client side Python applications to
communicate with the Data Dispatcher server. To use the API, you need to
install Data Dispatcher client module:

::: {.highlight-shell .notranslate}
::: highlight
    $ pip install --user datadispatcher
:::
:::

Then import the API module and create a `DataDispatcherClient`{.docutils
.literal .notranslate} object:

::: {.highlight-python .notranslate}
::: highlight
    from data_dispatcher.api import DataDispatcherClient
    client = DataDispatcherClient("http://server.host.domain:8080/dd/data")
:::
:::

*[class]{.pre}[ ]{.w}*[[data_dispatcher.api.]{.pre}]{.sig-prename .descclassname}[[DataDispatcherClient]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[server_url]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[auth_server_url]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[worker_id]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[worker_id_file]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[token]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[token_file]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[token_library]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[cpu_site]{.pre}]{.n}[[=]{.pre}]{.o}[[\'DEFAULT\']{.pre}]{.default_value}*, *[[timeout]{.pre}]{.n}[[=]{.pre}]{.o}[[300]{.pre}]{.default_value}*[)]{.sig-paren}

:   Initializes the DataDispatcherClient object

    Keyword Arguments[:]{.colon}

    :   -   **server_url** (*str*) -- The server endpoint URL. If
            unspecified, the value of the DATA_DISPATCHER_URL
            environment will be used

        -   **auth_server_url** (*str*) -- The endpoint URL for the
            Authentication server. If unspecified, the value of the
            DATA_DISPATCHER_AUTH_URL environment will be used

        -   **worker_id_file** (*str*) -- File path to read/store the
            worker ID. Default: \<cwd>/.data_dispatcher_worker_id

        -   **worker_id** (*str*) -- Worker ID to use when reserving
            next file. If unspecified, will be read from the worker ID
            file.

        -   **cpu_site** (*str*) -- Name of the CPU site where the
            client is running, optional. Will be used when reserving
            project files.

        -   **timeout** (*float* *or* *int*) -- Number of seconds to
            wait for a response.

    [[activate_project]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[project_id]{.pre}]{.n}*[)]{.sig-paren}

    :   Resets the state of an abandoned project back to "active"

    [[auth_info]{.pre}]{.sig-name .descname}[(]{.sig-paren}[)]{.sig-paren}

    :   Returns information about current authentication token.

        Returns[:]{.colon}

        :   -   *str* -- username of the authenticated user

            -   *numeric* -- token expiration timestamp

    [[cancel_project]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[project_id]{.pre}]{.n}*[)]{.sig-paren}

    :   Cancels a project by id

        Parameters[:]{.colon}

        :   **project_id** (*str*) -- project id

        Returns[:]{.colon}

        :   (dict) project information

    [[copy_project]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[project_id]{.pre}]{.n}*, *[[common_attributes]{.pre}]{.n}[[=]{.pre}]{.o}[[{}]{.pre}]{.default_value}*, *[[project_attributes]{.pre}]{.n}[[=]{.pre}]{.o}[[{}]{.pre}]{.default_value}*, *[[worker_timeout]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[idle_timeout]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*[)]{.sig-paren}

    :   Creates new project

        Parameters[:]{.colon}

        :   **project_id** (*int*) -- id of the project to copy

        Keyword Arguments[:]{.colon}

        :   -   **common_attributes** (*dict*) -- file attributes to
                override

            -   **project_attributes** (*dict*) -- project attributes to
                override

            -   **worker_timeout** (*int* *or* *float*) -- worker
                timeout to override

        Returns[:]{.colon}

        :   (dict) new project information

    [[create_project]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[files]{.pre}]{.n}*, *[[common_attributes]{.pre}]{.n}[[=]{.pre}]{.o}[[{}]{.pre}]{.default_value}*, *[[project_attributes]{.pre}]{.n}[[=]{.pre}]{.o}[[{}]{.pre}]{.default_value}*, *[[query]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[worker_timeout]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[idle_timeout]{.pre}]{.n}[[=]{.pre}]{.o}[[259200]{.pre}]{.default_value}*, *[[users]{.pre}]{.n}[[=]{.pre}]{.o}[[\[\]]{.pre}]{.default_value}*, *[[roles]{.pre}]{.n}[[=]{.pre}]{.o}[[\[\]]{.pre}]{.default_value}*[)]{.sig-paren}

    :   Creates new project

        Parameters[:]{.colon}

        :   -   **files** (*list*) -- Each item in the list is either a
                dictionary with keys: "namespace", "name", "attributes"
                (optional) or a string "namespace:name"

            -   **common_attributes** (*dict*) -- attributes to attach
                to each file, will be overridden by the individual file
                attribute values with the same key

            -   **project_attributes** (*dict*) -- attriutes to attach
                to the new project

            -   **query** (*str*) -- MQL query to be associated with the
                project. Thit attribute optiona and is not used by Data
                Dispatcher in any way. It is used for informational
                purposes only.

            -   **worker_timeout** (*int* *or* *float*) -- If not None,
                all file handles will be automatically released if
                allocated by same worker for longer than the
                `worker_timeout`{.docutils .literal .notranslate}
                seconds

            -   **idle_timeout** (*int* *or* *float*) -- If there is no
                file reserve/release activity for the specified time
                interval, the project goes into "abandoned" state.
                Default is 72 hours (3 days). If set to None, the
                project remains active until complete.

            -   **users** (*list* *of* *strings*) -- List of users who
                can use the worker interface (next_file, done,
                failed...), in addition to the project creator.

            -   **roles** (*list* *of* *strings*) -- List of roles,
                members of which are authorized to use the worker
                interface.

        Returns[:]{.colon}

        :   new project information

        Return type[:]{.colon}

        :   dict

    [[file_done]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[project_id]{.pre}]{.n}*, *[[did]{.pre}]{.n}*, *[[worker_id]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*[)]{.sig-paren}

    :   Notifies Data Dispatcher that the file was successfully
        processed and should be marked as "done".

        Parameters[:]{.colon}

        :   -   **project_id** (*int*) -- project id

            -   **did** (*str*) -- file DID ("\<namespace>:\<name>")

    [[file_failed]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[project_id]{.pre}]{.n}*, *[[did]{.pre}]{.n}*, *[[retry]{.pre}]{.n}[[=]{.pre}]{.o}[[True]{.pre}]{.default_value}*, *[[worker_id]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*[)]{.sig-paren}

    :   Notifies Data Dispatcher that the file was successfully
        processed and should be marked as "done".

        Parameters[:]{.colon}

        :   -   **project_id** (*int*) -- project id

            -   **did** (*str*) -- file DID ("\<namespace>:\<name>")

    [[get_file]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[namespace]{.pre}]{.n}*, *[[name]{.pre}]{.n}*[)]{.sig-paren}

    :   Deprecated

    [[get_handle]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[project_id]{.pre}]{.n}*, *[[namespace]{.pre}]{.n}*, *[[name]{.pre}]{.n}*[)]{.sig-paren}

    :   Gets information about a file handle

        Parameters[:]{.colon}

        :   -   **project_id** (*str*) -- project id

            -   **namespace** (*str*) -- file namespace

            -   **name** (*str*) -- file name

        Returns[:]{.colon}

        :   (dict) file handle information or None if not found

    [[get_project]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[project_id]{.pre}]{.n}*, *[[with_files]{.pre}]{.n}[[=]{.pre}]{.o}[[True]{.pre}]{.default_value}*, *[[with_replicas]{.pre}]{.n}[[=]{.pre}]{.o}[[False]{.pre}]{.default_value}*[)]{.sig-paren}

    :   Gets information about the project

        Parameters[:]{.colon}

        :   **project_id** (*str*) -- project id

        Keyword Arguments[:]{.colon}

        :   -   **with_files** (*boolean*) -- whether to include
                iformation about project files. Default: True

            -   **with_replicas** (*boolean*) -- whether to include
                iformation about project file replicas. Default: False

        Returns[:]{.colon}

        :   (dict) project information or None if project not found.

            The dictionary will include the following values:

            > <div>
            >
            > -   project_id: numeric, project id
            >
            > -   owner: str, project owner username,
            >
            > -   state: str, current project state,
            >
            > -   attributes: dict, project metadata attributes as set
            >     by the create_project(),
            >
            > -   created_timestamp: numeric, timestamp for the project
            >     creation time,
            >
            > -   ended_timestamp: numeric or None, project end
            >     timestamp,
            >
            > -   active: boolean, whether the project is active - at
            >     least one handle is not done or failed,
            >
            > -   query: str, MQL query string associated with the
            >     project,
            >
            > -   worker_timeout: numeric or None, worker idle timeout,
            >     in seconds
            >
            > -   idle_timeout: numeric or None, project inactivity
            >     timeout in seconds
            >
            > </div>

    [[get_rse]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[name]{.pre}]{.n}*[)]{.sig-paren}

    :   Returns information about RSE

        Parameters[:]{.colon}

        :   **name** (*str*) -- RSE name

        Returns[:]{.colon}

        :   dictionary with RSE information or None if not found

    [[list_handles]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[project_id]{.pre}]{.n}*, *[[state]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[not_state]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[with_replicas]{.pre}]{.n}[[=]{.pre}]{.o}[[False]{.pre}]{.default_value}*[)]{.sig-paren}

    :   Deprecated

    [[list_projects]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[owner]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[state]{.pre}]{.n}[[=]{.pre}]{.o}[[\'active\']{.pre}]{.default_value}*, *[[not_state]{.pre}]{.n}[[=]{.pre}]{.o}[[\'abandoned\']{.pre}]{.default_value}*, *[[attributes]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[with_files]{.pre}]{.n}[[=]{.pre}]{.o}[[True]{.pre}]{.default_value}*, *[[with_replicas]{.pre}]{.n}[[=]{.pre}]{.o}[[False]{.pre}]{.default_value}*[)]{.sig-paren}

    :   Lists existing projects

        Keyword Arguments[:]{.colon}

        :   -   **owner** (*str*) -- Include only projects owned by the
                specified user. Default: all users

            -   **state** (*str*) -- Include only projects in specified
                state. Default: active only

            -   **not_state** (*str*) -- Exclude projects in the
                specified state. Default: exclude abandoned

            -   **attributes** (*dict*) -- Include only projects with
                specified attribute values. Default: do not filter by
                attributes

            -   **with_files** (*boolean*) -- Include information about
                files. Default: True

            -   **with_replicas** (*boolean*) -- Include information
                about file replics. Default: False

        Returns[:]{.colon}

        :   list of dictionaries with information about projects
            selected

    [[list_rses]{.pre}]{.sig-name .descname}[(]{.sig-paren}[)]{.sig-paren}

    :   Return information about all RSEs

        Args:

        Returns[:]{.colon}

        :   list of dictionaries with RSE information

    [[login_digest]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[username]{.pre}]{.n}*, *[[password]{.pre}]{.n}*, *[[save_token]{.pre}]{.n}[[=]{.pre}]{.o}[[False]{.pre}]{.default_value}*[)]{.sig-paren}

    :   Performs password-based authentication and stores the
        authentication token locally.

        Parameters[:]{.colon}

        :   -   **username** (*str*)

            -   **password** (*str*) -- Password is not sent over the
                network. It is hashed and then used for digest
                authentication ([]{#index-0 .target}[**RFC
                2617**](https://datatracker.ietf.org/doc/html/rfc2617.html){.rfc
                .reference .external}).

        Returns[:]{.colon}

        :   -   *str* -- username of the authenticated user (same as
                `usernme`{.docutils .literal .notranslate} argument)

            -   *numeric* -- token expiration timestamp

    [[login_ldap]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[username]{.pre}]{.n}*, *[[password]{.pre}]{.n}*[)]{.sig-paren}

    :   Performs password-based authentication and stores the
        authentication token locally using LDAP.

        Parameters[:]{.colon}

        :   -   **username** (*str*)

            -   **password** (*str*) -- Password

        Returns[:]{.colon}

        :   -   *str* -- username of the authenticated user (same as
                `usernme`{.docutils .literal .notranslate} argument)

            -   *numeric* -- token expiration timestamp

    [[login_password]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[username]{.pre}]{.n}*, *[[password]{.pre}]{.n}*[)]{.sig-paren}

    :   Combines LDAP and []{#index-1 .target}[**RFC
        2617**](https://datatracker.ietf.org/doc/html/rfc2617.html){.rfc
        .reference .external} digest authentication by calling
        login_ldap first and then, if it fails, ldap_digest methods

        Parameters[:]{.colon}

        :   -   **username** (*str*)

            -   **password** (*str*) -- Password

        Returns[:]{.colon}

        :   -   *str* -- username of the authenticated user (same as
                `usernme`{.docutils .literal .notranslate} argument)

            -   *numeric* -- token expiration timestamp

    [[login_token]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[username]{.pre}]{.n}*, *[[encoded_token]{.pre}]{.n}*[)]{.sig-paren}

    :   Authenticate using a JWT or a SciToken.

        Parameters[:]{.colon}

        :   -   **username** (*str*)

            -   **encoded_token** (*str* *or* *bytes*)

        Returns[:]{.colon}

        :   -   *str* -- username of the authenticated user (same as
                `usernme`{.docutils .literal .notranslate} argument)

            -   *numeric* -- authentication expiration timestamp

    [[login_x509]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[username]{.pre}]{.n}*, *[[cert]{.pre}]{.n}*, *[[key]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*[)]{.sig-paren}

    :   Performs X.509 authentication and stores the authentication
        token locally.

        Parameters[:]{.colon}

        :   -   **username** (*str*)

            -   **cert** (*str*) -- Path to the file with the X.509
                certificate or the certificate and private key

            -   **key** (*str*) -- Path to the file with the X.509
                private key

        Returns[:]{.colon}

        :   -   *str* -- username of the authenticated user (same as
                `usernme`{.docutils .literal .notranslate} argument)

            -   *numeric* -- token expiration timestamp

    [[new_worker_id]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[new_id]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[worker_id_file]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*[)]{.sig-paren}

    :   Sets or generates new worker ID to be used for next file
        allocation.

        Keyword Arguments[:]{.colon}

        :   -   **new_id** (*str* *or* *None*) -- New worker id to use.
                If None, a random worker_id will be generated.

            -   **worker_id_file** (*str* *or* *None*) -- Path to store
                the worker id. Default:
                \<cwd>/.data_dispatcher_worker_id

        Returns[:]{.colon}

        :   (str) assigned worker id

    [[next_file]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[project_id]{.pre}]{.n}*, *[[cpu_site]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[worker_id]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[timeout]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[stagger]{.pre}]{.n}[[=]{.pre}]{.o}[[10]{.pre}]{.default_value}*[)]{.sig-paren}

    :   Reserves next available file from the project

        Parameters[:]{.colon}

        :   -   **project_id** (*int*) -- project id to reserve a file
                from

            -   **cpu_site** (*str*) -- optional, if specified, the file
                will be reserved according to the CPU/RSE proximity map

            -   **timeout** (*int* *or* *float*) -- optional, if
                specified, time to wait for a file to become available.
                Otherwise, will wait indefinitely

            -   **stagger** (*int* *or* *float*) -- optional, introduce
                a random delay between 0 and \<stagger> seconds before
                sending first request. This will help mitigate the
                effect of synchronous stard of multiple workers.
                Default: 10

        Returns[:]{.colon}

        :   Dictionary or boolean. If dictionary, the dictionary
            contains the reserved file information. "replicas" field
            will be a dictionary will contain a subdictionary with
            replicas information indexed by RSE name. If
            `True`{.docutils .literal .notranslate}: the request timed
            out, but can be retried. If `False`{.docutils .literal
            .notranslate}: the project has ended.

    *[static]{.pre}[ ]{.w}*[[random_worker_id]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[prefix]{.pre}]{.n}[[=]{.pre}]{.o}[[\'\']{.pre}]{.default_value}*[)]{.sig-paren}

    :   Static method to generate random worker id

    [[reserved_handles]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[project_id]{.pre}]{.n}*, *[[worker_id]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*[)]{.sig-paren}

    :   Returns list of file handles reserved in the project by given
        worker

        Parameters[:]{.colon}

        :   -   **project_id** (*int*) -- Project id

            -   **worker_id** (*str* *or* *None*) -- Worker id. If None,
                client's worker id will be used

        Returns[:]{.colon}

        :   list of dictionaries with the file handle information

    [[restart_handles]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[project_id]{.pre}]{.n}*, *[[done]{.pre}]{.n}[[=]{.pre}]{.o}[[False]{.pre}]{.default_value}*, *[[failed]{.pre}]{.n}[[=]{.pre}]{.o}[[False]{.pre}]{.default_value}*, *[[reserved]{.pre}]{.n}[[=]{.pre}]{.o}[[False]{.pre}]{.default_value}*, *[[all]{.pre}]{.n}[[=]{.pre}]{.o}[[False]{.pre}]{.default_value}*, *[[handles]{.pre}]{.n}[[=]{.pre}]{.o}[[\[\]]{.pre}]{.default_value}*[)]{.sig-paren}

    :   Restart processing of project file handles

        Parameters[:]{.colon}

        :   **project_id** (*int*) -- id of the project to restart

        Keyword Arguments[:]{.colon}

        :   -   **done** (*boolean*) -- default=False, restart done
                handles

            -   **reserved** (*boolean*) -- default=False, restart
                reserved handles

            -   **failed** (*boolean*) -- default=False, restart failed
                handles

            -   **all** (*boolean*) -- default=False, restart all
                handles

            -   **handles** (*list* *of* *DIDs*) -- default=\[\],
                restart specific handles

        Returns[:]{.colon}

        :   (dict) project information

    [[retry_request]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[method]{.pre}]{.n}*, *[[url]{.pre}]{.n}*, *[[timeout]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[\*\*]{.pre}]{.o}[[args]{.pre}]{.n}*[)]{.sig-paren}

    :   Implements the functionality to retry on 503 response with
        random exponentially growing delay Use timemout = 0 to try the
        request exactly once Returns the response with status=503 on
        timeout

    [[search_projects]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[search_query]{.pre}]{.n}*, *[[owner]{.pre}]{.n}[[=]{.pre}]{.o}[[None]{.pre}]{.default_value}*, *[[state]{.pre}]{.n}[[=]{.pre}]{.o}[[\'active\']{.pre}]{.default_value}*, *[[with_files]{.pre}]{.n}[[=]{.pre}]{.o}[[True]{.pre}]{.default_value}*, *[[with_replicas]{.pre}]{.n}[[=]{.pre}]{.o}[[False]{.pre}]{.default_value}*[)]{.sig-paren}

    :   Lists existing projects

        Parameters[:]{.colon}

        :   **search_query** (*str*) -- project search query in subset
            of MQL

        Keyword Arguments[:]{.colon}

        :   -   **owner** (*str*) -- Include only projects owned by the
                specified user. Default: all users

            -   **with_files** (*boolean*) -- Include information about
                files. Default: True

            -   **with_replicas** (*boolean*) -- Include information
                about file replics. Default: False

        Returns[:]{.colon}

        :   list of dictionaries with information about projects found

    [[set_rse_availability]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[name]{.pre}]{.n}*, *[[available]{.pre}]{.n}*[)]{.sig-paren}

    :   Changes RSE availability flag. The user must be an admin.

        Parameters[:]{.colon}

        :   -   **name** (*str*) -- RSE name

            -   **available** (*boolean*) -- RSE availability

        Returns[:]{.colon}

        :   dictionary with updated RSE information or None if not found

    [[version]{.pre}]{.sig-name .descname}[(]{.sig-paren}[)]{.sig-paren}

    :   Returns the server version as a string
:::

::: clearer
:::
:::
:::
:::

::: {.sphinxsidebar role="navigation" aria-label="Main"}
::: sphinxsidebarwrapper
<div>

#### Previous topic

[Data Dispatcher User Interface](ui.html "previous chapter")

</div>

<div>

#### Next topic

[File Processing with Data Dispatcher](worker.html "next chapter")

</div>

::: {role="note" aria-label="source link"}
### This Page

-   [Show Source](_sources/webapi.rst.txt)
:::

### Quick search {#searchlabel}

::: searchformwrapper
:::
:::
:::

::: clearer
:::
:::

::: {.related role="navigation" aria-label="Related"}
### Navigation

-   [index](genindex.html "General Index")
-   [next](worker.html "File Processing with Data Dispatcher") \|
-   [previous](ui.html "Data Dispatcher User Interface") \|
-   [Data Dispatcher documentation](index.html) »
-   [Python API]()
:::

::: {.footer role="contentinfo"}
© Copyright 2022, Igor Mandrichenko. Created using
[Sphinx](https://www.sphinx-doc.org/) 7.4.7.
:::
