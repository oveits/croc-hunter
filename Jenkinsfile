#!/usr/bin/groovy

// load pipeline functions
// Requires pipeline-github-lib plugin to load library from github

@Library('github.com/oveits/jenkins-pipeline@develop')

def pipeline = new io.estrado.Pipeline()

def configuration = [
  skipRemoveApp:true
]

// defaults
// configuration.skipRemoveApp    = pipeline.setConfiguration (configuration.skipRemoveApp, env.getProperty('SKIP_REMOVE_APP'), false)
configuration.skipRemoveApp    = configuration.skipRemoveApp != null ? configuration.skipRemoveApp : false


def branchNameNormalized = env.BRANCH_NAME.toLowerCase().replaceAll('/','-')
def uniqueBranchName = branchNameNormalized.take(20) + '-' + org.apache.commons.lang.RandomStringUtils.random(6, true, true).toLowerCase()
def sharedSelenium = true
def seleniumRelease
def seleniumNamespace = branchNameNormalized
// sharedSelenium ? seleniumRelease = 'selenium' : seleniumRelease='selenium-' + uniqueBranchName
seleniumRelease = branchNameNormalized + '-selenium'

podTemplate(label: 'jenkins-pipeline', 
  containers: [
    // containerTemplate(
    //   name: 'selenium-hub', 
    //   image: 'selenium/hub:latest', 
    //   // resourceRequestCpu: '200m', 
    //   // resourceLimitCpu: '300m', 
    //   // resourceRequestMemory: '256Mi', 
    //   // resourceLimitMemory: '512Mi',
    //   envVars: [
    //     // envVar(key: 'MYSQL_ALLOW_EMPTY_PASSWORD', value: 'true'),
    //     // secretEnvVar(key: 'MYSQL_PASSWORD', secretName: 'mysql-secret', secretKey: 'password'),
    //     // ...
    //     envVar(key: 'SE_OPTS', value: '-debug'),
    //     envVar(key: 'GRID_MAX_SESSION', value: '5')
    //   ],
    //   ports: [
    //     portMapping(name: 'selenium', containerPort: 4444, hostPort: 4444)
    //   ]
    // ),
    // containerTemplate(
    //   name: 'chrome-node', 
    //   image: 'selenium/node-chrome:latest',
    //   // resourceRequestCpu: '200m', 
    //   // resourceLimitCpu: '300m', 
    //   // resourceRequestMemory: '256Mi', 
    //   // resourceLimitMemory: '512Mi',
    //   command: 'bash -c "sleep 5 && /opt/bin/entry_point.sh"',
    //   ttyEnabled: true,
    //   envVars: [
    //     envVar(key: 'HUB_HOST', value: 'selenium-hub'),
    //     envVar(key: 'REMOTE_HOST', value: 'http://chrome-node:5555'),
    //     envVar(key: 'NODE_MAX_SESSION', value: '5'),
    //     envVar(key: 'NODE_MAX_INSTANCES', value: '5')
    //   ],
    //   ports: [
    //     portMapping(name: 'vnc', containerPort: 5900, hostPort: 5900),
    //     portMapping(name: 'chrome-node', containerPort: 5555, hostPort: 5555)
    //   ]
    // ),
    // containerTemplate(
    //   name: 'firefox-node', 
    //   image: 'selenium/node-firefox:latest', 
    //   // resourceRequestCpu: '200m', 
    //   // resourceLimitCpu: '300m', 
    //   // resourceRequestMemory: '256Mi', 
    //   // resourceLimitMemory: '512Mi',
    //   command: 'bash -c "sleep 5 && /opt/bin/entry_point.sh"',
    //   ttyEnabled: true,
    //   envVars: [
    //     envVar(key: 'HUB_HOST', value: 'selenium-hub'),
    //     envVar(key: 'REMOTE_HOST', value: 'http://firefox-node:5555'),
    //     envVar(key: 'NODE_MAX_SESSION', value: '5'),
    //     envVar(key: 'NODE_MAX_INSTANCES', value: '5')
    //   ],
    //   ports: [
    //     portMapping(name: 'vnc', containerPort: 5900, hostPort: 5901),
    //     portMapping(name: 'firefox-node', containerPort: 5555, hostPort: 5556)
    //   ]
    // ),
    containerTemplate(
      name: 'jnlp', 
      image: 'jenkinsci/jnlp-slave:3.19-1-alpine', 
      args: '${computer.jnlpmac} ${computer.name}', 
      workingDir: '/home/jenkins', 
      resourceRequestCpu: '200m', 
      resourceLimitCpu: '300m', 
      resourceRequestMemory: '256Mi', 
      resourceLimitMemory: '512Mi'
    ),
    containerTemplate(
      name: 'docker', 
      image: 'docker:latest', 
      command: 'cat', 
      ttyEnabled: true
    ),
    containerTemplate(
      name: 'golang', 
      image: 'golang:1.8.3', 
      command: 'cat', 
      ttyEnabled: true
    ),
    containerTemplate(
      name: 'helm', 
      image: 'lachlanevenson/k8s-helm:v2.12.1', 
      command: 'cat', 
      ttyEnabled: true
    ),
    containerTemplate(
      name: 'kubectl', 
      image: 'lachlanevenson/k8s-kubectl:v1.14.1', 
      command: 'cat', 
      ttyEnabled: true)
  ],
  volumes: [
    hostPathVolume(mountPath: '/var/run/docker.sock', hostPath: '/var/run/docker.sock'),
  ]
){

  node ('jenkins-pipeline') {

    def pwd = pwd()
    def chart_dir = "${pwd}/charts/croc-hunter"

    checkout scm

    // read in required jenkins workflow config values
    def inputFile = readFile('Jenkinsfile.json')
    def config = new groovy.json.JsonSlurperClassic().parseText(inputFile)
    println "pipeline config ==> ${config}"

    // continue only if pipeline enabled
    if (!config.pipeline.enabled) {
        println "pipeline disabled"
        return
    }

    // set additional git envvars for image tagging
    pipeline.gitEnvVars()

    // If pipeline debugging enabled
    if (config.pipeline.debug) {
      println "DEBUG ENABLED"
      sh "env | sort"

      println "Runing kubectl/helm tests"
      container('kubectl') {
        pipeline.kubectlTest()
      }
      container('helm') {
        pipeline.helmConfig()
      }
    }

    def acct = pipeline.getContainerRepoAcct(config)

    // tag image with version, and branch-commit_id
    def image_tags_map = pipeline.getContainerTags(config)

    // compile tag list
    def image_tags_list = pipeline.getMapValues(image_tags_map)

      // stage ('UI Tests') {
        
      //   // sh """
      //   //   test_pods=\$(helm status pr-6 -o json | jq -r .info.status.last_test_suite_run.results[].name)
      //   //   echo \$test_pods | xargs -n 1 kubectl -n \$namespace delete pod
      //   //   """
      //   def test_pods
      //   // container('helm') {
      //     //  Run helm tests

      //     if (config.app.test) {
      //       // clean from test pods
      //       def test_pods_before
      //       def namespace_before
      //       container('helm') {
      //         // debug
      //         sh "helm status ${branchNameNormalized} -o yaml"
      //         sh "helm status ${branchNameNormalized} -o yaml | grep ' name:' || true"
      //         sh "helm status ${branchNameNormalized} -o yaml | grep ' name:' | awk -F'[: ]+' '{print \$3}' || true"
      //         sh "helm status ${branchNameNormalized} -o yaml | grep 'namespace:' | awk -F': ' '{print \$2}'  || true"
      //         sh "NS=\$(helm status ${branchNameNormalized} -o yaml | grep 'namespace:' | awk -F': ' '{print \$2}'  || true) && echo -n \$NS"

      //         test_pods_before = sh script: "helm status ${branchNameNormalized} -o yaml | grep ' name:' | awk -F'[: ]+' '{print \$3}' || true", returnStdout: true
      //         namespace_before = sh script: "NS=\$(helm status ${branchNameNormalized} -o yaml | grep 'namespace:' | awk -F': ' '{print \$2}'  || true) && echo -n \$NS", returnStdout: true
              
      //         // debug
      //         echo "test_pods_before = ___${test_pods_before}___"
      //         echo "namespace_before = ___${namespace_before}___"
      //       }
      //       container('kubectl') {
      //         // debug
      //         echo "test_pods_before = ___${test_pods_before}___"
      //         echo "namespace_before = ___${namespace_before}___"
      //         sh "echo 'xargs -n 1 kubectl -n ${namespace_before} delete pod'"
      //         if (test_pods_before != null && test_pods_before != "") {
      //           // debug
      //           sh "echo -n '${test_pods_before}' | xargs -n 1 echo kubectl -n ${namespace_before} delete pod"

      //           sh "echo -n '${test_pods_before}' | xargs -n 1 kubectl -n ${namespace_before} delete pod"
      //         }
      //       }

      //       // run tests
      //       container('helm') {
      //         sh "helm test ${branchNameNormalized}"
      //       }

      //       // print results and delete pods:
      //       def test_pods_after
      //       def namespace_after
      //       container('helm') {
      //         test_pods_after = sh script: "helm status ${branchNameNormalized} -o yaml | grep ' name:' | awk -F'[: ]+' '{print \$3}'", returnStdout: true
      //         namespace_after = sh script: "helm status ${branchNameNormalized} -o yaml | grep 'namespace:' | awk -F': ' '{print \$2}'", returnStdout: true
      //       }
      //       container('kubectl') {
      //         sh "echo ${test_pods_after} | xargs -n 1 kubectl -n ${namespace_after} logs"
      //         sh "echo ${test_pods_after} | xargs -n 1 kubectl -n ${namespace_after} delete pod"
      //       }

      //       // pipeline.helmTest(
      //       //   name        : branchNameNormalized
      //       // )
      //       // TODO: OV: install jq in the helm container? Then activate following shell script to log the outcome of the tests:
      //       // sh """
      //       // test_pods=\$(helm status \${branchNameNormalized} -o json | jq -r .info.status.last_test_suite_run.results[].name)
      //       // namespace=\$(helm status \${branchNameNormalized} -o json | jq -r .namespace)

      //       // for test_pod in \$test_pods; do
      //       //   echo "Test Pod: \$test_pod"
      //       //   echo "============"
      //       //   echo ""
      //       //   kubectl -n \$namespace logs \$test_pod
      //       //   kubectl -n \$namespace delete pod \$test_pod
      //       //   echo ""
      //       //   echo "============"
      //       // done
      //       // """
      //     }
      //   // }
      //   // container('kubectl'){
      //   //     sh "kubectl logs ${branchNameNormalized}-croc-hunter-web-selenium-test --namespace ${branchNameNormalized}"
      //   // }
      // }

            // container('helm') {
            //   // debug
            //   def helmStatusText = sh "helm status pr-6 -o json" as String
            //   echo helmStatusText
            //   def helmStatus = readJSON text: helmStatusText
            //   echo "helmStatus.namespace = " + helmStatus.namespace
            //   echo "helmStatus.info.status.last_test_suite_run.results[].each{ result -> result.name } = " + helmStatus.info.status.last_test_suite_run.results[].each{ result -> result.name }
            // }

    stage ('compile and test') {

      container('golang') {
        sh "go test -v -race ./..."
        sh "make bootstrap build"
      }
    }

    stage ('test deployment') {

      container('helm') {

        // run helm chart linter
        pipeline.helmLint(chart_dir)

        // run dry-run helm chart installation
        pipeline.helmDeploy(
          dry_run       : true,
          name          : config.app.name,
          namespace     : config.app.name,
          chart_dir     : chart_dir,
          set           : [
            "imageTag": image_tags_list.get(0),
            "replicas": config.app.replicas,
            "cpu": config.app.cpu,
            "memory": config.app.memory,
            "ingress.hostname": config.app.hostname,
            "imagePullSecrets.name": config.k8s_secret.name,
            "imagePullSecrets.repository": config.container_repo.host,
            "imagePullSecrets.username": env.USERNAME,
            "imagePullSecrets.password": env.PASSWORD,
            "imagePullSecrets.email": "ServicePrincipal@AzureRM",
          ]
        )

      }
    }

    stage ('publish container') {

      container('docker') {

        // build and publish container
        pipeline.containerBuildPub(
            dockerfile: config.container_repo.dockerfile,
            host      : config.container_repo.host,
            acct      : acct,
            repo      : config.container_repo.repo,
            tags      : image_tags_list,
            auth_id   : config.container_repo.jenkins_creds_id,
            image_scanning: config.container_repo.image_scanning
        )
      }

    }

    if (env.BRANCH_NAME =~ "PR-*" ) {

      stage('PR: Deploy Selenium') {
        // Deploy using Helm chart
        container('helm') {
          // init
          println "initialzing helm client"
          sh "helm init"
          println "checking client/server version"
          sh "helm version"

          if ( !sharedSelenium ) {
            sh """
              # purge deleted versions of selenium, if present
              helm list -a | grep '^${seleniumRelease} ' && helm delete --purge ${seleniumRelease} || true
            """
          }

          // always:
          sh """
            # upgrade selenium revision. Install, if not present:
            helm upgrade --install ${seleniumRelease} stable/selenium \
              --namespace ${seleniumNamespace} \
              --set chromeDebug.enabled=true \
          """
          }
        
        // // wait for deployments
        // container('kubectl') {
        //   sh "kubectl rollout status --watch deployment/selenium-selenium-hub -n selenium --timeout=5m"
        //   sh "kubectl rollout status --watch deployment/selenium-selenium-chrome-debug -n selenium --timeout=5m"
        // }

      }

      stage ('PR: Deploy App') {
        // Deploy using Helm chart
        container('helm') {

          // purge deleted versions of ${branchNameNormalized}, if present
          sh """
            # purge deleted versions of ${branchNameNormalized}, if present
            helm list -a | grep '^${branchNameNormalized} ' && helm delete --purge ${branchNameNormalized} || true
          """

                    // Create secret from Jenkins credentials manager
          withCredentials([[$class          : 'UsernamePasswordMultiBinding', credentialsId: config.container_repo.jenkins_creds_id,
                        usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
          pipeline.helmDeploy(
            dry_run       : false,
            name          : branchNameNormalized,
            namespace     : branchNameNormalized,
            chart_dir     : chart_dir,
            set           : [
              "imageTag": image_tags_list.get(0),
              "replicas": config.app.replicas,
              "cpu": config.app.cpu,
              "memory": config.app.memory,
              "ingress.hostname": config.app.hostname,
              "imagePullSecrets.name": config.k8s_secret.name,
              "imagePullSecrets.repository": config.container_repo.host,
              "imagePullSecrets.username": env.USERNAME,
              "imagePullSecrets.password": env.PASSWORD,
              "imagePullSecrets.email": "ServicePrincipal@AzureRM",
              "test.seleniumHubUrl": "http://${seleniumRelease}-selenium-hub:4444/wd/hub",
              // "test.seleniumHubUrl": 'http://dev-node1.vocon-it.com:31881/wd/hub',
            ]
          )
          }
        }
      }

      stage ('PR: Selenium complete?') {
        // wait for Selenium deployments, if needed
        container('kubectl') {
          sh "kubectl rollout status --watch deployment/${seleniumRelease}-selenium-hub -n ${seleniumNamespace} --timeout=5m"
          sh "kubectl rollout status --watch deployment/${seleniumRelease}-selenium-chrome-debug -n ${seleniumNamespace} --timeout=5m"
        }
      }

      // stage ('Simple curl Tests') {
      //   container('helm') {
      //     //  Run helm tests
      //     if (config.app.test) {
      //       pipeline.helmTest(
      //         name        : branchNameNormalized
      //       )
      //     }
      //   }
      // }

      stage ('Create and Push Selenium Test Docker Image') {
        container('docker') {
          pipeline.containerBuildPub(
              dockerfile: config.test_container_repo.dockerfile,
              host      : config.test_container_repo.host,
              acct      : acct,
              repo      : config.test_container_repo.repo,
              tags      : image_tags_list,
              auth_id   : config.test_container_repo.jenkins_creds_id,
              image_scanning: config.test_container_repo.image_scanning
          )
        }
      }

      stage ('UI Tests') {
        
        def test_pods
        // container('helm') {
          //  Run helm tests

          if (config.app.test) {
            // clean old test pods
            def test_pods_before
            def namespace_before
            container('helm') {
              // debug
              // def helmStatusText = sh "helm status ${branchNameNormalized} -o json"
              // def helmStatus = readJSON text: helmStatusText
              // echo "helmStatus.namespace = " + helmStatus.namespace
              // echo "helmStatus.info.status.last_test_suite_run.results[].each{ result -> result.name } = " + helmStatus.info.status.last_test_suite_run.results[].each{ result -> result.name }
              sh "helm status ${branchNameNormalized} -o yaml"
              sh "helm status ${branchNameNormalized} -o yaml | grep ' name:' || true"
              sh "helm status ${branchNameNormalized} -o yaml | grep ' name:' | awk -F'[: ]+' '{print \$3}' || true"
              sh "helm status ${branchNameNormalized} -o yaml | grep 'namespace:' | awk -F': ' '{print \$2}'  || true"
              sh "NS=\$(helm status ${branchNameNormalized} -o yaml | grep 'namespace:' | awk -F': ' '{print \$2}'  || true) && echo -n \$NS"

              // with jq: test_pods=\$(helm status \${branchNameNormalized} -o json | jq -r .info.status.last_test_suite_run.results[].name)
              test_pods_before = sh script: "helm status ${branchNameNormalized} -o yaml | grep ' name:' | awk -F'[: ]+' '{print \$3}' || true", returnStdout: true
              // with jq: namespace=\$(helm status \${branchNameNormalized} -o json | jq -r .namespace)
              namespace_before = sh script: "NS=\$(helm status ${branchNameNormalized} -o yaml | grep 'namespace:' | awk -F': ' '{print \$2}'  || true) && echo -n \$NS", returnStdout: true
              
              // debug
              echo "test_pods_before = ___${test_pods_before}___"
              echo "namespace_before = ___${namespace_before}___"
            }
            container('kubectl') {
              // debug
              echo "test_pods_before = ___${test_pods_before}___"
              echo "namespace_before = ___${namespace_before}___"
              sh "echo 'xargs -n 1 kubectl -n ${namespace_before} delete pod'"
              if (test_pods_before != null && test_pods_before != "") {
                // debug
                sh "echo -n '${test_pods_before}' | xargs -n 1 echo kubectl -n ${namespace_before} delete pod"

                sh "echo -n '${test_pods_before}' | xargs -n 1 kubectl -n ${namespace_before} delete pod"
              }
            }

            // run tests
            container('helm') {
              sh "helm test ${branchNameNormalized}"
            }

            // print results and delete pods:
            def test_pods_after
            def namespace_after
            container('helm') {
              test_pods_after = sh script: "helm status ${branchNameNormalized} -o yaml | grep ' name:' | awk -F'[: ]+' '{print \$3}'", returnStdout: true
              namespace_after = sh script: "helm status ${branchNameNormalized} -o yaml | grep 'namespace:' | awk -F': ' '{print \$2}'", returnStdout: true
            }
            container('kubectl') {
              sh "echo ${test_pods_after} | xargs -n 1 kubectl -n ${namespace_after} logs"
              sh "echo ${test_pods_after} | xargs -n 1 kubectl -n ${namespace_after} delete pod"
            }

            // pipeline.helmTest(
            //   name        : branchNameNormalized
            // )
            // TODO: OV: install jq in the helm container? Then activate following shell script to log the outcome of the tests:
            // sh """
            // test_pods=\$(helm status \${branchNameNormalized} -o json | jq -r .info.status.last_test_suite_run.results[].name)
            // namespace=\$(helm status \${branchNameNormalized} -o json | jq -r .namespace)

            // for test_pod in \$test_pods; do
            //   echo "Test Pod: \$test_pod"
            //   echo "============"
            //   echo ""
            //   kubectl -n \$namespace logs \$test_pod
            //   kubectl -n \$namespace delete pod \$test_pod
            //   echo ""
            //   echo "============"
            // done
            // """
          }
        // }
        // container('kubectl'){
        //     sh "kubectl logs ${branchNameNormalized}-croc-hunter-web-selenium-test --namespace ${branchNameNormalized}"
        // }
      }

      // stage ('UI Tests') {
        
      //   // sh """
      //   //   test_pods=\$(helm status pr-6 -o json | jq -r .info.status.last_test_suite_run.results[].name)
      //   //   echo \$test_pods | xargs -n 1 kubectl -n \$namespace delete pod
      //   //   """
      //   def test_pods
      //   // container('helm') {
      //     //  Run helm tests

      //     if (config.app.test) {
      //       // clean from test pods
      //       def test_pods_before
      //       def namespace_before
      //       container('helm') {
      //         // debug
      //         sh "helm status ${branchNameNormalized} -o yaml"
      //         sh "helm status ${branchNameNormalized} -o yaml | grep ' name:' || true"
      //         sh "helm status ${branchNameNormalized} -o yaml | grep ' name:' | awk -F'[: ]*' '{print \$3}' || true"

      //         test_pods_before = sh script: "helm status ${branchNameNormalized} -o yaml | grep ' name:' | awk -F'[: ]*' '{print \$3}' || true", returnStdout: true
      //         namespace_before = sh script: "helm status ${branchNameNormalized} -o yaml | grep 'namespace:' | awk -F'[: ]*' '{print \$2}'  || true", returnStdout: true
              
      //         // debug
      //         echo "test_pods_before = ___${test_pods_before}___"
      //         echo "namespace_before = ___${namespace_before}___"
      //       }
      //       container('kubectl') {
      //         // debug
      //         echo "test_pods_before = ___${test_pods_before}___"
      //         echo "namespace_before = ___${namespace_before}___"
      //         sh "echo 'xargs -n 1 kubectl -n ${namespace_before} delete pod'"
      //         sh "echo ${test_pods_before} | xargs -n 1 echo kubectl -n ${namespace_before} delete pod"

      //         sh "echo ${test_pods_before} | xargs -n 1 kubectl -n ${namespace_before} delete pod"
      //       }

      //       // run tests
      //       container('helm') {
      //         sh "helm test ${branchNameNormalized}"
      //       }

      //       // print results and delete pods:
      //       def test_pods_after
      //       def namespace_after
      //       container('helm') {
      //         test_pods_after = sh script: "helm status ${branchNameNormalized} -o yaml | grep ' name:' | awk -F'[: ]*' '{print \$3}'", returnStdout: true
      //         namespace_after = sh script: "helm status ${branchNameNormalized} -o yaml | grep 'namespace:' | awk -F'[: ]*' '{print \$2}'", returnStdout: true
      //       }
      //       container('kubectl') {
      //         sh "echo ${test_pods_after} | xargs -n 1 kubectl -n ${namespace_after} logs"
      //         sh "echo ${test_pods_after} | xargs -n 1 kubectl -n ${namespace_after} delete pod"
      //       }

      //       // pipeline.helmTest(
      //       //   name        : branchNameNormalized
      //       // )
      //       // TODO: OV: install jq in the helm container? Then activate following shell script to log the outcome of the tests:
      //       // sh """
      //       // test_pods=\$(helm status \${branchNameNormalized} -o json | jq -r .info.status.last_test_suite_run.results[].name)
      //       // namespace=\$(helm status \${branchNameNormalized} -o json | jq -r .namespace)

      //       // for test_pod in \$test_pods; do
      //       //   echo "Test Pod: \$test_pod"
      //       //   echo "============"
      //       //   echo ""
      //       //   kubectl -n \$namespace logs \$test_pod
      //       //   kubectl -n \$namespace delete pod \$test_pod
      //       //   echo ""
      //       //   echo "============"
      //       // done
      //       // """
      //     }
      //   // }
      //   // container('kubectl'){
      //   //     sh "kubectl logs ${branchNameNormalized}-croc-hunter-web-selenium-test --namespace ${branchNameNormalized}"
      //   // }
      // }

      if (configuration.skipRemoveApp == false) {
        stage ('PR: Remove App') {
          container('helm') {
            // delete test deployment
            pipeline.helmDelete(
                name       : branchNameNormalized
            )
          }
        }
      }

      if ( !sharedSelenium ) {
        stage('Remove Selenium') {
          // Delete Helm revision
          container('helm') {
            // init
            println "initialzing helm client"
            sh "helm init"
            println "checking client/server version"
            sh "helm version"
            
            println "deleting and purging selenium, if present"
            sh """
              # purge deleted versions of selenium, if present
              helm list -a | grep '^${seleniumRelease} ' && helm delete --purge ${seleniumRelease} || true
            """
          }
        }
      }
    }

    // deploy only the master branch
    if (env.BRANCH_NAME == 'master') {
      stage ('deploy to k8s') {
          // Deploy using Helm chart
        container('helm') {
                    // Create secret from Jenkins credentials manager
          withCredentials([[$class          : 'UsernamePasswordMultiBinding', credentialsId: config.container_repo.jenkins_creds_id,
                        usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
          pipeline.helmDeploy(
            dry_run       : false,
            name          : config.app.name,
            namespace     : config.app.name,
            chart_dir     : chart_dir,
            set           : [
              "imageTag": image_tags_list.get(0),
              "replicas": config.app.replicas,
              "cpu": config.app.cpu,
              "memory": config.app.memory,
              "ingress.hostname": config.app.hostname,
              "imagePullSecrets.name": config.k8s_secret.name,
              "imagePullSecrets.repository": config.container_repo.host,
              "imagePullSecrets.username": env.USERNAME,
              "imagePullSecrets.password": env.PASSWORD,
              "imagePullSecrets.email": "ServicePrincipal@AzureRM",
            ]
          )
          
            //  Run helm tests
            if (config.app.test) {
              pipeline.helmTest(
                name          : config.app.name
              )
            }
          }
        }
      }
    }
  }
}
