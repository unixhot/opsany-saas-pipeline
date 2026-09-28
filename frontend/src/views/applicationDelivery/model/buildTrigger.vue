<template>
    <!-- buildTrigger 构建触发 -->
    <div>
        <h4 style="padding: 0 0 0 26px">
            {{ language.build_label1 }}：<a-switch
                @change="onisTriggerChange"
                v-model="isTrigger"
                style="margin: 0 10px 0 0"
            ></a-switch>
        </h4>
        <div v-if="isTrigger" style="padding: 20px 0 0 26px; color: #888">
            <div>
                <span>{{ language.build_label2 }}：</span>
                <a-select
                    @change="assemblyLineValueChange"
                    mode="multiple"
                    v-model="assemblyLineValue"
                    :placeholder="language.build_placeholder"
                    style="width: 600px; margin: 0 0 20px 0"
                    optionFilterProp="label"
                    showSearch
                >
                    <a-select-option
                        :title="item.fullname + ' ('+ (item.application && item.application.visible_name || '--') +')'"
                        v-for="item in assemblyLineList"
                        :key="item.fullname"
                        :value="item.fullname"
                        :label="item.fullname"
                    >
                        {{ item.fullname }} ({{item.application && item.application.visible_name || '--'}})
                    </a-select-option>
                </a-select>
            </div>
            <a-radio-group
                @change="triggerTypeChange"
                class="line_feed"
                :options="options"
                v-model="triggerType"
            ></a-radio-group>
        </div>
    </div>
</template>

<script>
import { getAllAssemblyLine } from '@/api/assemblyLine'
export default {
    data() {
        return {
            isTrigger: false,
            assemblyLineList: [],
            assemblyLineValue: [],
            triggerType: 1,
        }
    },
    computed: {
        options() {
            return [
                { label: this.language.build_options1, value: 1 },
                { label: this.language.build_options2, value: 2 },
                { label: this.language.build_options3, value: 3 },
            ]
        },
    },
    created() {
        this.language = this.$store.state.language.languageAuth.pipelineConfiguration || {}
    },
    mounted() {
        this.getAllAssemblyLineData()
    },
    props: ['ReverseBuildTrigger'],
    watch: {
        ReverseBuildTrigger: {
            handler(val, oldval) {
                if (val.threshold) {
                    this.isTrigger = true
                    if (val.upstreamProjects) {
                        this.assemblyLineValue = val.upstreamProjects.split(',')
                    }
                    if (val.threshold.name == 'SUCCESS') {
                        this.triggerType = 1
                    } else if (val.threshold.name == 'UNSTABLE') {
                        this.triggerType = 2
                    } else if (val.threshold.name == 'FAILURE') {
                        this.triggerType = 3
                    }
                }
            },
            deep: true,
        },
    },
    methods: {
        // 是否构建触发
        onisTriggerChange(val) {
            this.isTrigger = val
            if (!this.isTrigger) {
                this.$emit('update:ReverseBuildTrigger', {})
            } else {
                this.$emit('update:ReverseBuildTrigger', {
                    spec: null,
                    upstreamProjects: '',
                    threshold: {
                        name: 'SUCCESS',
                        ordinal: '0',
                        color: 'BLUE',
                        completeBuild: 'true',
                    },
                })
            }
        },
        // 触发类型change
        triggerTypeChange() {
            let obj
            if (this.triggerType == 1) {
                obj = {
                    name: 'SUCCESS',
                    ordinal: '0',
                    color: 'BLUE',
                    completeBuild: 'true',
                }
            } else if (this.triggerType == 2) {
                obj = {
                    name: 'UNSTABLE',
                    ordinal: '1',
                    color: 'YELLOW',
                    completeBuild: 'true',
                }
            } else if (this.triggerType == 3) {
                obj = {
                    name: 'FAILURE',
                    ordinal: '2',
                    color: 'RED',
                    completeBuild: 'true',
                }
            }
            this.$set(this.ReverseBuildTrigger, 'threshold', obj)
        },
        // 选择流水线change
        assemblyLineValueChange() {
            this.ReverseBuildTrigger.upstreamProjects = this.assemblyLineValue.join(',')
        },
        // 获取所有流水线
        getAllAssemblyLineData() {
            getAllAssemblyLine().then((res) => {
                if (res.code == 200 && res.data) {
                    this.assemblyLineList = res.data.jobs?.job_list.filter(item =>{
                        return item.name != this.$route.query.name
                    })
                }
            })
        },
    },
}
</script>

<style lang="less" scoped>
</style>