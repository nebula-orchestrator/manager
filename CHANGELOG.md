# Change Log

## [Unreleased](https://github.com/nebula-orchestrator/manager/tree/HEAD)

[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/2.5.0...HEAD)

**Implemented enhancements:**

- Add cron jobs endpoints & modify the device\_group endpoints to include that option [\#29](https://github.com/nebula-orchestrator/manager/issues/29)
- Bump parse-it from 0.5.11 to 0.7.0 [\#40](https://github.com/nebula-orchestrator/manager/pull/40) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump flask-httpauth from 3.2.4 to 3.3.0 [\#39](https://github.com/nebula-orchestrator/manager/pull/39) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump flask from 1.0.2 to 1.0.3 [\#38](https://github.com/nebula-orchestrator/manager/pull/38) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump requests from 2.21.0 to 2.22.0 [\#37](https://github.com/nebula-orchestrator/manager/pull/37) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump websocket-client from 0.54.0 to 0.56.0 [\#36](https://github.com/nebula-orchestrator/manager/pull/36) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump werkzeug from 0.15.2 to 0.15.4 [\#35](https://github.com/nebula-orchestrator/manager/pull/35) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump backports-ssl-match-hostname from 3.5.0.1 to 3.7.0.1 [\#34](https://github.com/nebula-orchestrator/manager/pull/34) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump parse-it from 0.5.5 to 0.5.11 [\#33](https://github.com/nebula-orchestrator/manager/pull/33) ([dependabot[bot]](https://github.com/apps/dependabot))

## [2.5.0](https://github.com/nebula-orchestrator/manager/tree/2.5.0) (2019-04-21)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/2.4.0...2.5.0)

**Implemented enhancements:**

- multiple users\permissions support [\#2](https://github.com/nebula-orchestrator/manager/issues/2)

## [2.4.0](https://github.com/nebula-orchestrator/manager/tree/2.4.0) (2019-03-27)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/2.3.0...2.4.0)

## [2.3.0](https://github.com/nebula-orchestrator/manager/tree/2.3.0) (2019-03-11)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/2.2.0...2.3.0)

**Implemented enhancements:**

- Optional reporting architecture [\#30](https://github.com/nebula-orchestrator/manager/issues/30)
- Move automatic Docker imags build from Docker Hub to Travis-CI [\#25](https://github.com/nebula-orchestrator/manager/issues/25)
- Multiple authentication methods  [\#3](https://github.com/nebula-orchestrator/manager/issues/3)

## [2.2.0](https://github.com/nebula-orchestrator/manager/tree/2.2.0) (2019-02-27)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/2.1.0...2.2.0)

**Implemented enhancements:**

- Migrate to Python 3.x [\#20](https://github.com/nebula-orchestrator/manager/issues/20)

## [2.1.0](https://github.com/nebula-orchestrator/manager/tree/2.1.0) (2019-02-17)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/2.0.0...2.1.0)

**Implemented enhancements:**

- Give sane defaults to some app confiugrations and allow apps to be POST created\updated without them being mandatory declared [\#27](https://github.com/nebula-orchestrator/manager/issues/27)
- Add automated unit tests [\#24](https://github.com/nebula-orchestrator/manager/issues/24)

## [2.0.0](https://github.com/nebula-orchestrator/manager/tree/2.0.0) (2019-01-14)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/2.0.1...2.0.0)

## [2.0.1](https://github.com/nebula-orchestrator/manager/tree/2.0.1) (2019-01-14)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/1.6.0...2.0.1)

**Implemented enhancements:**

- Rename api-manager to manager [\#21](https://github.com/nebula-orchestrator/manager/issues/21)
- pod like stracture option [\#6](https://github.com/nebula-orchestrator/manager/issues/6)

**Fixed bugs:**

- Allow starting the manager with no conf.json file present [\#22](https://github.com/nebula-orchestrator/manager/issues/22)

**Merged pull requests:**

- 2.0.0a [\#23](https://github.com/nebula-orchestrator/manager/pull/23) ([naorlivne](https://github.com/naorlivne))

## [1.6.0](https://github.com/nebula-orchestrator/manager/tree/1.6.0) (2018-12-06)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/1.5.0...1.6.0)

## [1.5.0](https://github.com/nebula-orchestrator/manager/tree/1.5.0) (2018-10-07)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/1.4.0...1.5.0)

## [1.4.0](https://github.com/nebula-orchestrator/manager/tree/1.4.0) (2018-08-21)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/1.3.0...1.4.0)

**Implemented enhancements:**

- update all prereqs versions [\#15](https://github.com/nebula-orchestrator/manager/issues/15)

**Fixed bugs:**

- RabbitMQ connections are not closed properly  [\#16](https://github.com/nebula-orchestrator/manager/issues/16)
- Set /api/status to work without basic Auth [\#5](https://github.com/nebula-orchestrator/manager/issues/5)

## [1.3.0](https://github.com/nebula-orchestrator/manager/tree/1.3.0) (2018-07-24)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/1.2.0...1.3.0)

**Implemented enhancements:**

- Return a list of what paramaters are missing rather then a generic message in case of missing parameters on app creation\update [\#12](https://github.com/nebula-orchestrator/manager/issues/12)

**Fixed bugs:**

- add protection against missing fanout exchanges [\#9](https://github.com/nebula-orchestrator/manager/issues/9)

## [1.2.0](https://github.com/nebula-orchestrator/manager/tree/1.2.0) (2017-10-19)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/1.1.1...1.2.0)

**Implemented enhancements:**

- Version lock all required pip\apt-get dependencies in the Dockerfile [\#11](https://github.com/nebula-orchestrator/manager/issues/11)
- Some Nebula config paramters should be optional/have default [\#8](https://github.com/nebula-orchestrator/manager/issues/8)

**Fixed bugs:**

-  Remove unneeded modules from requirements.txt file [\#7](https://github.com/nebula-orchestrator/manager/issues/7)

**Closed issues:**

- enable "durable" flag in RabbitMQ exchange [\#13](https://github.com/nebula-orchestrator/manager/issues/13)

## [1.1.1](https://github.com/nebula-orchestrator/manager/tree/1.1.1) (2017-09-18)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/1.1.0...1.1.1)

## [1.1.0](https://github.com/nebula-orchestrator/manager/tree/1.1.0) (2017-09-18)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/1.0.0...1.1.0)

## [1.0.0](https://github.com/nebula-orchestrator/manager/tree/1.0.0) (2017-08-16)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/0.9.0...1.0.0)

## [0.9.0](https://github.com/nebula-orchestrator/manager/tree/0.9.0) (2017-08-03)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/0.8.0...0.9.0)

**Implemented enhancements:**

- PUT update support [\#1](https://github.com/nebula-orchestrator/manager/issues/1)

## [0.8.0](https://github.com/nebula-orchestrator/manager/tree/0.8.0) (2017-06-19)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/0.7...0.8.0)

## [0.7](https://github.com/nebula-orchestrator/manager/tree/0.7) (2017-05-29)
[Full Changelog](https://github.com/nebula-orchestrator/manager/compare/v0.7...0.7)

## [v0.7](https://github.com/nebula-orchestrator/manager/tree/v0.7) (2017-05-29)


\* *This Change Log was automatically generated by [github_changelog_generator](https://github.com/skywinder/Github-Changelog-Generator)*