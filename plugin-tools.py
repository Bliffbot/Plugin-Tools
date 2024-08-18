import os
import shutil
import datetime
import sys
import xml.etree.ElementTree as ET
import json5
import paramiko
import stat
from mcrcon import MCRcon

def log(text):
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {text}")

def logo():
	log(f"Plugin-Tools by Bliffbot")
	log(f"Version 2.1.1")
	log(f"")
	log(f"loading config...")


def help():
	log(f"no args detected")
	log(f"USAGE")
	log(f"plugin-tools.py \"path/to/config.json\"")
	log(f"the config file will be set to a default if it is empty")
	log(f"the following pip packages are required: json5, mcrcon, paramiko")
	exit()


def newConfig():
	log(f"config file not found or empty")

	defaults = '''// YOU MIGHT HAVE TO REMOVE ALL COMMENTS FROM THIS FILE
{
	// just the name of your plugin without anything else like version numbers
	"pluginName": "best plugin",

	// the folder in which intellij put the compiled jar files
	"jarFolder": "C:/intellij/projects/best plugin/target",

	// the path to the pom.xml which has all of your maven config
	"pomXML": "C:/intellij/projects/best plugin/pom.xml",

	// true		- the script automatically sets the next version in the pom.xml
	// false	- the pom.xml remains untouched
	// supported version formats: 1.0.0 or 1.0.0.beta.0
	// the last number will be incremented by one: 1.0.1 or 1.0.0.beta.1
	// everything else is ignored so you could put 'the.BEST.plugin.EVER.0' and it would still work
	"setNextVersion": "true",

	// put all the folders where you want the latest version of your plugin to be copied to in here
	"folders": {

		"folder name": {

			// put the path of your folder in here
			"path": "C:/minecraft server/plugins",

			// the folder might not be on the local machine and instead on an sftp server
			// set the following options if this is the case
			"sftp": {
				"enabled": "false",
				"ip": "127.0.0.1",
				"port": "22",
				"username": "user",
				"password": "password"
			},

			// old		- the script looks for all .jar-files starting with the the name of your plugin and append them with .old
			// delete	- the script looks for all .jar-files starting with the the name of your plugin and delete them
			// false	- the script will not search the folder for these .jar-files
			"tidy": "delete",

			// true		- the script will copy the latest version of your plugin to this folder (after tidy ran)
			// false	- the script will not copy the latest version of your plugin to this folder
			"copy": "true"
		}
	},

	// you can execute a command on a server using rcon if you want
	"servers": {

		// the name is only used for logging purposes
		"server name": {

			// set the rcon options to allow the script to connect to the server
			"enabled": "false",
			"ip": "127.0.0.1",
			"port": "25575",
			"password": "password",

			// it is possible to execute multiple commands
			"command": ["reload confirm", "say SERVER IS READY"]
		}
	}
}'''

	try:
		with open(sys.argv[1], "w") as configFile:
			configFile.write(defaults)
		log(f"new config file generated at {sys.argv[1]}")
	except Exception as error:
		log(f"could not generate new config file - {error}")

	log(f"finished :)")
	exit()


def getConfig():
	if not os.path.exists(sys.argv[1]):
		newConfig()

	with open(sys.argv[1], "r") as configFile:
		content = configFile.read()

	if content == "":
		newConfig()

	with open(sys.argv[1], "r") as configFile:
		config = json5.load(configFile)

	log(f"config loaded")
	log(f"Plugin Name: {config["pluginName"]}")
	log(f"Source Folder: {config["jarFolder"]}")
	log(f"POM Location: {config["pomXML"]}")
	return config


def pom(config):
	log(f"getting plugin version...")

	if not os.path.exists(config["pomXML"]):
		log(f"pom.xml not found - please check your config")
		exit()

	tree = ET.parse(f"{config["pomXML"]}")

	if tree is None:
		log(f"pom.xml could not be parsed")
		exit()

	root = tree.getroot()
	namespace = root.tag[root.tag.find("{")+1:root.tag.find("}")]
	version_element = root.find(f"{{{namespace}}}version")

	if version_element is None:
		log(f"plugin version could not be found in the pom.xml")
		exit()

	pluginVersion = version_element.text

	if pluginVersion is None:
		log(f"plugin version seem to be not set in the pom.xml")
		exit()

	log(f"Plugin Version: {pluginVersion}")

	if config["setNextVersion"] == "false":
		return pluginVersion

	version = pluginVersion.split(".")

	try:
		versionInt = int(version[-1])
	except:
		log(f"weird version in pom.xml -> did not modify")
		log(f"please use major.minor.patch.test.revision")
		log(f"the parts need to be separated by dots")
		log(f"and there must be a number after the last dot")
		log(f"e.g. 1.2.3 or 1.2.3.beta.4")
		return pluginVersion

	version[-1] = str(versionInt + 1)
	newVersion = ".".join(version)

	log(f"Next Version: {newVersion}")
	version_element.text = newVersion

	try:
		tree.write("pom.xml", xml_declaration = True, encoding = "utf-8", method = "xml", default_namespace = namespace)
		log(f"the next plugin version has been set in the pom.xml")

	except:
		log(f"could not update the plugin version in the pom.xml")

	return pluginVersion


def sftp(config, folder):
	log(f"sftp connecting...")

	try:
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(config["folders"][folder]["sftp"]["ip"], int(config["folders"][folder]["sftp"]["port"]), config["folders"][folder]["sftp"]["username"], config["folders"][folder]["sftp"]["password"])
	
		sftp = ssh.open_sftp()
		log(f"sftp connected")
		return sftp

	except Exception as error:
		log(f"sftp not connected, see error...")
		log(error)
		return False


def tidy(config, folder):
	folderPath = config["folders"][folder]["path"]

	if not folderPath.endswith("/"):
		folderPath = folderPath + "/"

	if config["folders"][folder]["sftp"]["enabled"] == "false":
		if config["folders"][folder]["tidy"] != "old" and config["folders"][folder]["tidy"] != "delete":
			log(f"not tidying local folder")
			return

		log(f"tidying local folder...")

		for file in os.listdir(folderPath):
			path = folderPath + file
			if file.startswith(config['pluginName']) and os.path.isfile(path) and file.endswith(".jar"):
				if config["folders"][folder]["tidy"] == "old":
					try:
						shutil.move(path, path + ".old")
						log(f"{file} renamed")
					except Exception as error:
						log(f"{file} not renamed - {error}")

				if config["folders"][folder]["tidy"] == "delete":
					try:
						os.remove(path)
						log(f"{file} deleted")
					except Exception as error:
						log(f"{file} not deleted - {error}")

		log(f"tidied local folder")
	
	else:
		if config["folders"][folder]["tidy"] != "old" and config["folders"][folder]["tidy"] != "delete":
			log(f"not tidying sftp folder")
			return

		log(f"tidying sftp folder...")
		sftp_connection = sftp(config, folder)

		if sftp_connection != False:

			for file in sftp_connection.listdir(folderPath):
				path = folderPath + file
				if file.startswith(config["pluginName"]) and stat.S_ISREG(sftp_connection.stat(path).st_mode) and file.endswith(".jar"):
					if config["folders"][folder]["tidy"] == "old":
						try:
							sftp_connection.rename(path, path + ".old")
							log(f" {file} renamed")
						except Exception as error:
							log(f"{file} not renamed - {error}")

					if config["folders"][folder]["tidy"] == "delete":
						try:
							sftp_connection.remove(path)
							log(f"{file} deleted")
						except Exception as error:
							log(f"{file} not deleted - {error}")

			log(f"tidied sftp folder")
			sftp_connection.close()
		
		else:
			log(f"could not tidy sftp folder")


def copy(config, folder, jarFolder, fileName):
	if config["folders"][folder]["sftp"]["enabled"] == "false":
		if config["folders"][folder]["copy"] == "false":
			log(f"not copying to local folder")
			return

		log(f"copying to local folder...")

		folderPath = config["folders"][folder]["path"]

		if not folderPath.endswith("/"):
			folderPath = folderPath + "/"

		try:
			shutil.copy(jarFolder + fileName, folderPath)
			log(f"copied to local folder")

		except Exception as error:
			log(error)
	
	else:
		sftp_connection = sftp(config, folder)

		if sftp_connection != False:

			if config["folders"][folder]["copy"] == "false":
				log(f"not copying to sftp folder")
				return

			log(f"copying to sftp folder...")

			folderPath = config["folders"][folder]["path"]

			if not folderPath.endswith("/"):
				folderPath = folderPath + "/"

			try:
				sftp_connection.put(jarFolder + fileName, folderPath + fileName)
				log(f"copied to sftp folder")

			except Exception as error:
				log(error)

			sftp_connection.close()
		
		else:
			log(f"could not copy to sftp folder")


def folders(config, pluginVersion):
	fileName = f"{config['pluginName']}-{pluginVersion}.jar"
	log(f"File Name: {fileName}")

	jarFolder = config['jarFolder']

	if not jarFolder.endswith("/"):
		jarFolder = jarFolder + "/"

	jarPath = f"{jarFolder}{fileName}"

	if not os.path.exists(jarPath):
		log(f"jar not found")
		return

	log(f"jar found")
	log(f"modifying the folders...")

	for folder in config["folders"]:
		log(f"{folder} - {config["folders"][folder]["path"]}")
		tidy(config, folder)
		copy(config, folder, jarFolder, fileName)


def command(options, server):
	log(f"Server: {server}")

	for command in options["command"]:
		log(f"Command: {command}")
		
		try:
			with MCRcon(options["ip"], options["password"], port = int(options["port"])) as mcr:
				response = mcr.command(command)
				log(response)
		except Exception as error:
			log(f"could not send command, see error...")
			log(error)




def servers(config):
	log(f"sending server commands...")

	for server in config["servers"]:
		command(config["servers"][server], server)

	log(f"all commands sent")


def main():
	os.system("cls")

	logo()

	if len(sys.argv) < 2:
		help()

	elif len(sys.argv) > 1:
		config = getConfig()

	pluginVersion = pom(config)
	folders(config, pluginVersion)
	servers(config)

	log(f"finished :)")


main()