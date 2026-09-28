<template>
    <!-- pipelineConfiguration 流水线配置 -->
    <div class="main">
        <header>
            <p style="font-size:20px;margin:0;">
                <span>{{$route.query.name}}</span>
                <a-button style="float:right;" icon="arrow-left" @click="routerBack">返回</a-button>
            </p>
        </header>
        <div class="main-content">
            <a-tabs default-active-key="2" >
                <a-tab-pane key="1" :tab="language.tabsList1">
                    <BasicInformation></BasicInformation>
                </a-tab-pane>
                <a-tab-pane key="2" :tab="language.tabsList2">
                    <ProcessConfiguration></ProcessConfiguration>
                </a-tab-pane>
                <a-tab-pane key="3" :tab="language.tabsList3">
                    <TriggerRule></TriggerRule>
                </a-tab-pane>
                <a-tab-pane key="4" :tab="language.tabsList4">
                    <ParameterSetting></ParameterSetting>
                </a-tab-pane>
            </a-tabs>
        </div>
    </div>
</template>

<script>
import BasicInformation from "./model/basicInformation.vue"
import ProcessConfiguration from "./model/processConfiguration.vue"
import TriggerRule from "./model/triggerRule.vue"
import ParameterSetting from "./model/parameterSetting.vue"
export default {
    data() {
        return {

        }
    },
    beforeRouteEnter(to,from,next) {
        next(vm=>{
            vm.$router.replace({path:to.path,query:{...vm.$route.query,fromName:from.name}})
        })
    },
    created() {
        this.language = this.$store.state.language.languageAuth.pipelineConfiguration || {}
    },
    methods: {
        tabClick(e) {
            console.log(e)
        },
        routerBack() {
            let query = JSON.parse(JSON.stringify(this.$route.query))
            if(query.fromName == "assemblyLine" || query.fromName == "myCollection"){
                delete query.fromName
                delete query.fromTitle
                delete query.name
                this.$router.push({name:this.$route.query.fromName,query:query})
            }else {
                this.$router.go(-1)
            }
        },

    },
    components: {

        BasicInformation, ProcessConfiguration,TriggerRule,ParameterSetting
    }
}
</script>

<style scoped lang="less">
.main {
    background: #fff;
    header {
        border-bottom: 1px solid #ccc;
        padding: 20px;
        span{
            font-weight: 1000;
            font-size: 24px;
        }
    }
    .main-content {
        padding: 20px;
    }
}
</style>