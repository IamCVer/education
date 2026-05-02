<template>
  <md-card class="md-card-profile">
    <div class="md-card-avatar">
      <img class="img" :src="cardUserImage" />
    </div>

    <md-card-content>
      <h6 class="category text-gray">首席执行官 / 联合创始人</h6>
      <h4 class="card-title">张三</h4>
      <p class="card-description">
        致力于推动技术创新，专注于人工智能和大数据领域的研究与应用。
        相信技术能够改变世界，让生活更美好。
      </p>
      <md-button class="md-round md-success">关注</md-button>
    </md-card-content>
  </md-card>
</template>
<script>
export default {
  name: "user-card",
  props: {
    cardUserImage: {
      type: String,
      default: require("@/assets/img/faces/marc.jpg"),
    },
  },
  data() {
    return {};
  },
};
</script>
<style></style>
