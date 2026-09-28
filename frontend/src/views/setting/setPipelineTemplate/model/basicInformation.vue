<template>
    <!-- basicInformation 基础信息 -->
    <div>
        <a-form :form="basicInformationForm" :label-col="{ span: 5 }" :wrapper-col="{ span: 12 }">
            <a-form-item label="模板名称">
                <a-input
                    placeholder="请输入模板名称,仅支持中文、数字、字母、下划线、中划线。"
                    v-decorator="['name', { rules: [{ required: true, pattern: /^[0-9a-zA-Z-_\u4e00-\u9fff]{1,}$/, message: '请输入模板名称,仅支持中文、数字、字母、下划线、中划线。' },{ max: 50,message: '模板名称长度限制在50个字符以内。',}] }]"
                ></a-input>
            </a-form-item>
            <a-form-item label="所属分组">
                <a-select
                    placeholder="请选择所属分组"
                    v-decorator="['group_id', { rules: [{ required: true, message: '请选择分组' }] }]"
                    optionFilterProp="label"
                    showSearch
                >
                    <a-select-option
                        v-for="(item, index) in groupList"
                        :value="item.code"
                        :key="index"
                        :label="item.name"
                        >{{ item.name }}</a-select-option
                    >
                </a-select>
            </a-form-item>
            <a-form-item label="模板描述">
                <a-textarea
                    placeholder="描述长度限制在一百字内"
                    :rows="6"
                    v-decorator="['description', { rules: [{ required: false, message: '请输入描述' }] }]"
                ></a-textarea>
            </a-form-item>
        </a-form>
    </div>
</template>

<script>
import { getPipelineTemplateGroup, addTemplate } from '@/api/pipelineTemplate.js'
import storage from 'store'
export default {
    data() {
        return {
            basicInformationForm: this.$form.createForm(this, { name: 'basicInformationForm' }),
            // 分组选项
            groupList: [],
        }
    },
    props: ['templateData'],
    watch: {
        templateData(val, oldval) {
            this.basicInformationForm.setFieldsValue({
                name: val.name,
                group_id: val.group && val.group.code,
                description: val.description,
            })
        },
    },
    mounted() {
        this.getBasicInformationData()
        this.getGroupList()
        if(this.$route.query.groupCode) {
            this.$nextTick(()=>{
                this.basicInformationForm.setFieldsValue( { group_id:this.$route.query.groupCode - 0, })
            })
            
        }
    },
    methods: {
        // 获取分组选项
        getGroupList() {
            getPipelineTemplateGroup({ group: true }).then((res) => {
                if ((res.code = 200 && res.data)) {
                    let built_in = window.sessionStorage.getItem('is_inner_pipeline') == 'true' ? true : false
                    this.groupList = res.data.filter((item) => {
                        return item.built_in === built_in
                    })
                }
            })
        },
        // 获取数据并回显
        getBasicInformationData() {
            // getBasicInformation({ job_name: this.$route.query.name, code: storage.get('__applicationInfo').code }).then(res => {
            //     if (res.code == 200 && res.data) {
            //         this.basicInformationForm.setFieldsValue({ name: res.data.name, description: res.data.description })
            //     }
            // })
        },
    },
}
</script>

<style lang="less" scoped>
</style>