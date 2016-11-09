import datetime
import getopt
import os
import socket
import subprocess
import sys

# append worker binary source path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# since we are using the worker httpclient, worker_version is expected to be in the configuration
from worker import configuration
configuration.set_config({configuration.WORKER_VERSION: "LinuxAutoRegister"})

from worker import CurlHttpClient
from worker import simplejson as json

REGISTER = "register"
DEREGISTER = "deregister"


def get_cert_info(certificate_path):
    """Gets certificate information by invoking OpenSSL (OMS agent dependency).

    Returns:
        A tuple containing the certificate's issuer, subject and thumbprint.
    """
    p = subprocess.Popen(["openssl", "x509", "-noout", "-in", certificate_path, "-fingerprint", "-sha1"],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    raw_fingerprint, e = p.communicate()

    if p.poll() != 0:
        raise Exception("Unable to get certificate thumbprint.")
    thumbprint = raw_fingerprint.split("SHA1 Fingerprint=")[1].replace(":", "").strip()

    p = subprocess.Popen(["openssl", "x509", "-noout", "-in", certificate_path, "-issuer"],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    raw_issuer, e = p.communicate()

    if p.poll() != 0:
        raise Exception("Unable to get certificate issuer.")
    issuer = raw_issuer.split("issuer= ")[1].strip()

    p = subprocess.Popen(["openssl", "x509", "-noout", "-in", certificate_path, "-subject"],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    raw_subject, e = p.communicate()

    if p.poll() != 0:
        raise Exception("Unable to get certificate subject.")
    subject = raw_subject.split("subject= ")[1].strip()

    return issuer, subject, thumbprint


def get_headers_and_payload(worker_group_name, certificate_path):
    """Formats the required headers and payload for the registration and deregitration requests.

    Returns:
        A tuple containing a dictionary for the request headers and a dictionary for the payload (request body).
    """
    issuer, subject, thumbprint = get_cert_info(certificate_path)
    headers = {'ProtocolVersion': "2.0",
               'x-ms-date': datetime.datetime.utcnow().isoformat() + "0-00:00",
               "Content-Type": "application/json"}

    payload = {'RunbookWorkerGroup': worker_group_name,
               "MachineName": socket.gethostname(),
               "IpAddress": socket.gethostbyname(socket.gethostname()),
               "Thumbprint": thumbprint,
               "Issuer": issuer,
               "Subject": subject}

    return headers, payload


def register(registration_endpoint, worker_group_name, machine_id, cert_path, key_path, test_mode):
    """Registers the worker through the automation linked account with the Agent Service.

    Returns:
        The deserialized response from the Agent Service.
    """
    headers, payload = get_headers_and_payload(worker_group_name, cert_path)
    url = registration_endpoint + "/HybridV2(MachineId='" + machine_id + "')"

    http_client = CurlHttpClient(cert_path, key_path, test_mode)
    response = http_client.put(url, headers=headers, data=payload)

    if response.status_code != 200:
        raise Exception("Unable to register [reason=" + response.raw_data + "]")

    return json.loads(response.raw_data)


def deregister(registration_endpoint, worker_group_name, machine_id, cert_path, key_path, test_mode):
    """Deregisters the worker through the automation linked account with the Agent Service.

    Note:
        This method is only present for testing purposes for now. Linked account deregistration is not yet implemented
        and deregistration need to be made through using the automation account information.

    Returns:

    """
    headers, payload = get_headers_and_payload(worker_group_name, cert_path)
    url = registration_endpoint + "/Hybrid(MachineId='" + machine_id + "')"

    http_client = CurlHttpClient(cert_path, key_path, test_mode)
    response = http_client.delete(url, headers=headers, data=payload)

    if response.status_code != 200:
        raise Exception("Unable to deregister [reason=" + response.raw_data + "]")


def create_worker_configuration_file(working_directory, jrds_uri, registration_endpoint, workspace_id,
                                     automation_account_id, worker_group_name, machine_id, oms_cert_path, oms_key_path):
    """Creates the automation hybrid worker configuration file.

    Note:
        The generated file has to match the latest worker.conf template.
    """
    issuer, subject, thumbprint = get_cert_info(oms_cert_path)

    conf = open(os.path.join(working_directory, "worker.conf"), "w")
    conf.write("[configuration]\n")
    conf.write("jrds_cert_path=" + oms_cert_path + "\n")
    conf.write("jrds_key_path=" + oms_key_path + "\n")
    conf.write("jrds_base_uri=" + jrds_uri + "\n")
    conf.write("account_id=" + automation_account_id + "\n")
    conf.write("machine_id=" + machine_id + "\n")
    conf.write("hybrid_worker_group_name=" + worker_group_name + "\n")
    conf.write("working_dir=" + working_directory + "\n")
    conf.write("bypass_certificate_verification=False\n")
    conf.write("debug_traces=True\n")
    conf.write("\n")

    conf.write("[OMSMetadata]\n")
    conf.write("agent_id = " + machine_id + "\n")
    conf.write("workspace_id = " + workspace_id + "\n")
    conf.write("registration_endpoint = " + registration_endpoint + "\n")
    conf.write("oms_cert_thumbprint = " + thumbprint + "\n")


def main(argv):
    agent_id = None
    oms_cert_path = None
    oms_key_path = None
    operation = None
    test_mode = False
    working_directory = None
    workspace_id = None

    # parse cmd line args
    try:
        opts, args = getopt.getopt(argv, "hrdw:a:c:k:p:t",
                                   ["help", "register", "deregister", "workspaceid=", "agentid=", "certpath=",
                                    "keypath=", "path="])
    except getopt.GetoptError:
        print __file__ + "[--register, --deregister] -w <workspaceid> -a <agentid> -c <certhpath> -k <keypath> -p <path>"
        sys.exit(2)
    for opt, arg in opts:
        if opt == ("-h", "--help"):
            print __file__ + "[--register, --deregister] -w <workspaceid> -a <agentid> -c <certhpath> -k <keypath> -p <path>"
            sys.exit()
        elif opt in ("-r", "--register"):
            operation = REGISTER
        elif opt in ("-d", "--deregister"):
            operation = DEREGISTER
        elif opt in ("-w", "--workspaceid"):
            workspace_id = arg
        elif opt in ("-a", "--agentid"):
            agent_id = arg
        elif opt in ("-c", "--certpath"):
            oms_cert_path = arg
        elif opt in ("-k", "--keypath"):
            oms_key_path = arg
        elif opt in ("-p", "--path"):
            working_directory = arg
        elif opt in ("-t", "--test"):
            test_mode = True

    if workspace_id is None or agent_id is None or oms_cert_path is None or oms_key_path is None\
            or working_directory is None:
        print "Missing mandatory arguments."
        print "Use -h or --help for usage."
        sys.exit(1)
    else:
        # validate that the cert and key exists
        if os.path.isfile(oms_cert_path) is False or os.path.isfile(oms_key_path) is False:
            raise Exception("Certificate or key file doesn't exist. Are you using absolute path?")

        # build registration endpoint
        if test_mode is True:
            registration_endpoint = "https://oaasagentsvcdf.test.azure-automation.net/accounts/" + workspace_id + "/"
        else:
            registration_endpoint = "https://" + workspace_id + ".agentsvc.azure-automation.net/accounts/" +\
                                    workspace_id + "/"

        # rename to match oms concepts to automation
        machine_id = agent_id
        worker_group_name = socket.gethostname() + "_" + agent_id

        # action
        if operation == REGISTER:
            registration_response = register(registration_endpoint, worker_group_name, machine_id, oms_cert_path,
                                             oms_key_path, test_mode)
            create_worker_configuration_file(working_directory, registration_response["jobRuntimeDataServiceUri"],
                                             registration_endpoint, workspace_id, registration_response["AccountId"],
                                             worker_group_name, machine_id, oms_cert_path, oms_key_path)
        elif operation == DEREGISTER:
            deregister(registration_endpoint, worker_group_name, machine_id, oms_cert_path, oms_key_path, test_mode)
        else:
            raise Exception("No option specified, specify --register, --deregister or --help.")


if __name__ == "__main__":
    main(sys.argv[1:])
