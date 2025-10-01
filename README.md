More information about SQLution can be found at: 
[valentin-herrmann.com/sqlution](https://valentin-herrmann.com/sqlution/). 

The latest(minor) release is hosted at: [sqlution.de](https://sqlution.de/).

#### Deployment
The application is developed to be hosted via an Ubuntu server with nginx. For deployment, the steps described at [github.com/TheProtonGuy/Django_Ubuntu_Server_Deployment](https://github.com/TheProtonGuy/Django_Ubuntu_Server_Deployment) can be followed. The resource requirements are very low and for most use cases a small server (1vCPU, 1GB RAM, 10GB Disk) is sufficient. When logging in as admin into the WebApp the resource usage is displayed monitored, logged and can be downloaded as csv file.

#### Versioning
The version number is stored in the VERSION file. The versioning follows the semantic versioning scheme (**major.intermediate.minor**). The minor number is incremented for small changes like aesthetics, small bug fixes or performance improvements. The intermediate number is incremented for bigger features or several smaller features/bugfixes. The major number is incremented for breaking changes, disrupting features or major changes to the UI/UX. If backwards compatibility is broken it is mentioned in the release notes.

The release notes of intermediate versions list all changes since the last intermediate version. Planned intermediate versions are tracked as github milestones.

#### Contributing
Feel free to contribute to the project by forking it and creating a pull request. For larger changes please open an issue first to discuss the proposed changes. If you don't want to contribute code, you can also help by reporting bugs or suggesting features via the issue tracker.