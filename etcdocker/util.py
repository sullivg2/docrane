import docker
import etcd

def _get_docker_client():
    # Assume docker is local
    return docker.Client()


def get_containers():
    client = _get_docker_client()
    return client.containers(all=True)


def get_container_names(containers):
    # Returns list of container names from etcd key list
    container_names = []
    for container in containers:
        container_names.append(container['key'].rsplit('/')[-1])

    return container_names


def get_etcd_container_names(base_key_dir):
    """
    Get container name list from etcd

    args:
        base_key_dir (str) - etcd path for etcdocker

    Returns: (list)
        List of container names
    """
    # Returns list of container names from etcd key list
    client = etcd.Client()
    # Get container key list
    containers = get_container_names(client.read(
        base_key_dir, recursive=True, sorted=True)._children)

    container_names = []
    for container in containers:
        container_names.append(container['key'].rsplit('/')[-1])

    return container_names


def get_params(container_path):
    """
    Get params for container from etcd

    args:
        container_path (str) - etcd path to container params

    Returns: (dict)
        Raw etcd params
    """
    client = etcd.Client()
    children = client.read(container_path)._children
    params = {}

    for child in children:
        name = child['key'].rsplit('/')[-1]
        params[name] = child['value']

    return params


def convert_params(params):
    """
    Converts etcd params to docker params

    args:
        params (dict) - raw etcd key value pairs

    Returns: (dict)
        Converted docker params
    """
    converted_params = {
        'ports': None,
        'volumes_from': None,
        'volumes': None}

    for param in params.iterkeys():
        if params.get(param) and param in converted_params.keys():
            try:
                converted_params[param] = ast.literal_eval(
                    params.get(param))
            except ValueError:
                pass
        else:
            converted_params[param] = params.get(param)

    return converted_params


def create_docker_container(name, params):
    """
    Create a Docker container

    args:
        name (str) - Name of container
        params (dict) - Docker params
    """
    client = _get_docker_container()
    client.create_container(
        image=params.get('image'),
        detach=True,
        volumes=params.get('volumes'),
        ports=params.get('ports').keys(),
        name=name)


def start_docker_container(name, params):
    """
    Start a Docker container

    args:
        name (str) - Name of container
        params (dict) - Docker params
    """
    client = _get_docker_container()
    client.start(
        container=name,
        port_bindings=params.get('ports'),
        volumes_from=params.get('volumes_from'),
        privileged=params.get('privileged'))


def stop_and_rm_docker_container(name):
    """
    Stop and remove a Docker container

    args:
        name (str) - Name of container
    """
    client = _get_docker_container()
    client.stop(name, 5)
    client.remove_container(name)
